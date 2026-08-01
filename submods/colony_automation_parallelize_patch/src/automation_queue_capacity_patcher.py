#!/usr/bin/env python3
"""Locate and optionally apply the Stellaris automation queue-capacity patch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86 import (
    X86_OP_IMM,
    X86_OP_MEM,
    X86_OP_REG,
    X86_REG_AL,
    X86_REG_EAX,
    X86_REG_RAX,
    X86_REG_RCX,
    X86_REG_RIP,
)


class ScanError(RuntimeError):
    pass


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def u64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def align_up(value: int, alignment: int) -> int:
    if alignment <= 0 or alignment & (alignment - 1):
        raise ScanError(f"invalid power-of-two alignment: 0x{alignment:X}")
    return (value + alignment - 1) & -alignment


@dataclass(frozen=True)
class Section:
    name: str
    virtual_address: int
    virtual_size: int
    raw_offset: int
    raw_size: int
    characteristics: int

    @property
    def executable(self) -> bool:
        return bool(self.characteristics & 0x20000000)


class PEImage:
    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        if self.data[:2] != b"MZ":
            raise ScanError("input is not a DOS/PE image")
        self.pe_offset = u32(self.data, 0x3C)
        if self.data[self.pe_offset : self.pe_offset + 4] != b"PE\0\0":
            raise ScanError("PE signature is missing")
        self.coff_offset = self.pe_offset + 4
        if u16(self.data, self.coff_offset) != 0x8664:
            raise ScanError("only AMD64 PE images are supported")
        self.section_count = u16(self.data, self.coff_offset + 2)
        optional_size = u16(self.data, self.coff_offset + 16)
        self.optional_offset = self.coff_offset + 20
        if u16(self.data, self.optional_offset) != 0x20B:
            raise ScanError("only PE32+ images are supported")
        self.image_base = u64(self.data, self.optional_offset + 24)
        self.size_of_code = u32(self.data, self.optional_offset + 4)
        self.section_alignment = u32(self.data, self.optional_offset + 32)
        self.file_alignment = u32(self.data, self.optional_offset + 36)
        self.size_of_image = u32(self.data, self.optional_offset + 56)
        self.size_of_headers = u32(self.data, self.optional_offset + 60)
        self.section_table_offset = self.optional_offset + optional_size
        sections = []
        for index in range(self.section_count):
            entry = self.section_table_offset + index * 40
            name = self.data[entry : entry + 8].split(b"\0", 1)[0].decode(
                "ascii", errors="replace"
            )
            sections.append(
                Section(
                    name=name,
                    virtual_size=u32(self.data, entry + 8),
                    virtual_address=u32(self.data, entry + 12),
                    raw_size=u32(self.data, entry + 16),
                    raw_offset=u32(self.data, entry + 20),
                    characteristics=u32(self.data, entry + 36),
                )
            )
        self.sections = tuple(sections)

    def executable_sections(self) -> Iterable[Section]:
        return (section for section in self.sections if section.executable)

    def rva_to_offset(self, rva: int) -> int:
        for section in self.sections:
            size = max(section.virtual_size, section.raw_size)
            if section.virtual_address <= rva < section.virtual_address + size:
                delta = rva - section.virtual_address
                if delta >= section.raw_size:
                    raise ScanError(f"RVA 0x{rva:X} has no file-backed bytes")
                return section.raw_offset + delta
        raise ScanError(f"RVA 0x{rva:X} is not in a section")

    def va_to_offset(self, va: int) -> int:
        return self.rva_to_offset(va - self.image_base)

    def offset_to_rva(self, offset: int) -> int:
        for section in self.sections:
            if section.raw_offset <= offset < section.raw_offset + section.raw_size:
                return section.virtual_address + offset - section.raw_offset
        raise ScanError(f"file offset 0x{offset:X} is not in a section")

    def bytes_at_va(self, va: int, size: int) -> bytes:
        offset = self.va_to_offset(va)
        return self.data[offset : offset + size]


@dataclass(frozen=True)
class BytePattern:
    values: bytes
    masks: bytes

    @classmethod
    def parse(cls, expression: str) -> "BytePattern":
        values = bytearray()
        masks = bytearray()
        for token in expression.split():
            if token in {"?", "??"}:
                values.append(0)
                masks.append(0)
            else:
                if len(token) != 2:
                    raise ValueError(f"invalid pattern token: {token}")
                values.append(int(token, 16))
                masks.append(0xFF)
        return cls(bytes(values), bytes(masks))

    def find_all(self, data: bytes) -> list[int]:
        width = len(self.values)
        if not width:
            return []
        hits = []
        for start in range(len(data) - width + 1):
            if all(
                not mask or data[start + index] == value
                for index, (value, mask) in enumerate(zip(self.values, self.masks))
            ):
                hits.append(start)
        return hits


# The colony-state register is compiler allocation, not an ABI. This is only a
# byte-level prefilter; the candidate is accepted below after decoding its
# data/control-flow shape and recovering the register from decoded operands.
SCHEDULER_ANCHOR_PATTERN = BytePattern.parse(
    """
    E8 ?? ?? ?? ??
    84 C0
    0F 85 ?? ?? ?? ??
    """
)

PROGRESSION_PATTERN = BytePattern.parse(
    """
    48 8D 51 ??
    4C 89 7C 24 ??
    45 84 C9
    75 ??
    8B 0A
    49 8D 40 ??
    39 08
    48 8D 54 24 ??
    89 4C 24 ??
    48 0F 4C D0
    44 8B 3A
    41 FF CF
    """
)

KNOWN_PROFILES = {
    "BC451C72D9654C8901F1BB0BEE1DD78D76F415465C2FBF746E9F98ADE333173A": {
        "name": "Stellaris 4.4.6",
        "role": "regression baseline only",
    }
}

STEAM_LIBRARY_PATH_RE = re.compile(r'"path"\s*"(?P<path>(?:\\.|[^"])*)"')


def scan_pattern(image: PEImage, pattern: BytePattern, label: str) -> tuple[Section, int]:
    hits: list[tuple[Section, int]] = []
    for section in image.executable_sections():
        raw = image.data[section.raw_offset : section.raw_offset + section.raw_size]
        hits.extend((section, offset) for offset in pattern.find_all(raw))
    if len(hits) != 1:
        addresses = [
            f"0x{image.image_base + section.virtual_address + offset:X}"
            for section, offset in hits[:10]
        ]
        raise ScanError(
            f"{label} signature produced {len(hits)} matches"
            + (f": {', '.join(addresses)}" if addresses else "")
        )
    return hits[0]


def make_disassembler() -> Cs:
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    return disassembler


def direct_call_target(instruction) -> int | None:
    if instruction.mnemonic != "call" or len(instruction.operands) != 1:
        return None
    operand = instruction.operands[0]
    return operand.imm if operand.type == X86_OP_IMM else None


def memory_displacement(instruction, *, base: int | None = None) -> int | None:
    for operand in instruction.operands:
        if operand.type == X86_OP_MEM and (base is None or operand.mem.base == base):
            return operand.mem.disp
    return None


def rip_target(instruction) -> int | None:
    for operand in instruction.operands:
        if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
            return instruction.address + instruction.size + operand.mem.disp
    return None


def direct_branch_target(instruction) -> int | None:
    if not instruction.mnemonic.startswith("j") or len(instruction.operands) != 1:
        return None
    operand = instruction.operands[0]
    return operand.imm if operand.type == X86_OP_IMM else None


def instructions_ending_at(image: PEImage, address: int) -> list:
    """Return decodable x64 instructions ending exactly at *address*."""
    candidates = []
    for width in range(1, 16):
        start = address - width
        if start < image.image_base:
            break
        try:
            instructions = list(
                make_disassembler().disasm(image.bytes_at_va(start, width), start)
            )
        except ScanError:
            continue
        if len(instructions) == 1 and instructions[0].address + instructions[0].size == address:
            candidates.append(instructions[0])
    return candidates


def scheduler_candidate(image: PEImage, call_va: int) -> dict | None:
    """Decode and validate the local scheduler guard shape around *call_va*."""
    try:
        code = image.bytes_at_va(call_va, 0x30)
    except ScanError:
        return None
    instructions = list(make_disassembler().disasm(code, call_va))
    if len(instructions) < 5:
        return None

    call, test, occupied_exit, count_check, disabled_exit = instructions[:5]
    loads = instructions_ending_at(image, call_va)
    load = next(
        (
            instruction
            for instruction in loads
            if instruction.mnemonic == "mov"
            and len(instruction.operands) == 2
            and instruction.operands[0].type == X86_OP_REG
            and instruction.operands[0].reg == X86_REG_RCX
            and instruction.operands[1].type == X86_OP_MEM
            and instruction.operands[1].mem.disp == 8
        ),
        None,
    )
    if load is None:
        return None
    if (
        direct_call_target(call) is None
        or test.mnemonic != "test"
        or len(test.operands) != 2
        or any(operand.type != X86_OP_REG or operand.reg != X86_REG_AL for operand in test.operands)
    ):
        return None

    colony_register = load.operands[1].mem.base
    if colony_register == 0:
        return None
    if (
        count_check.mnemonic != "cmp"
        or len(count_check.operands) != 2
        or count_check.operands[0].type != X86_OP_MEM
        or count_check.operands[0].mem.base != colony_register
        or count_check.operands[0].mem.disp != 0x24
        or count_check.operands[1].type != X86_OP_IMM
        or count_check.operands[1].imm != 0
    ):
        return None

    first_exit = direct_branch_target(occupied_exit)
    second_exit = direct_branch_target(disabled_exit)
    if first_exit is None or first_exit != second_exit:
        return None

    call_bytes = image.bytes_at_va(call_va, 5)
    return {
        "signature_va": load.address,
        "call_va": call_va,
        "call_rva": call_va - image.image_base,
        "call_file_offset": image.va_to_offset(call_va),
        "call_bytes": call_bytes,
        "guard_va": direct_call_target(call),
        "colony_register": make_disassembler().reg_name(colony_register),
        "scheduler_exit_va": first_exit,
    }


def locate_scheduler(image: PEImage) -> dict:
    candidates: list[dict] = []
    for section in image.executable_sections():
        raw = image.data[section.raw_offset : section.raw_offset + section.raw_size]
        for relative in SCHEDULER_ANCHOR_PATTERN.find_all(raw):
            call_va = image.image_base + section.virtual_address + relative
            candidate = scheduler_candidate(image, call_va)
            if candidate is not None:
                candidates.append(candidate)
    if len(candidates) != 1:
        addresses = ", ".join(
            f"0x{candidate['signature_va']:X}" for candidate in candidates[:10]
        )
        raise ScanError(
            f"scheduler structural scan produced {len(candidates)} matches"
            + (f": {addresses}" if addresses else "")
        )
    return candidates[0]


def validate_guard(image: PEImage, guard_va: int, expected_count_offset: int) -> dict:
    code = image.bytes_at_va(guard_va, 0x500)
    instructions = list(make_disassembler().disasm(code, guard_va))
    if not instructions or instructions[0].address != guard_va:
        raise ScanError("could not disassemble the guard target")

    resolver = None
    colony_reference_offset = None
    queue_handle_offset = None
    queue_registry_va = None
    mask_seen = False
    item_offset_seen = False
    count_offset_seen = False
    registry_bound_seen = False
    registry_entries_seen = False
    registry_slot_seen = False
    queue_identity_seen = False
    rtti_calls = 0
    true_return_seen = False
    false_return_seen = False

    for index, instruction in enumerate(instructions):
        if instruction.address >= guard_va + 0x400:
            break

        if (
            instruction.mnemonic == "mov"
            and len(instruction.operands) == 2
            and instruction.operands[0].type == X86_OP_REG
            and instruction.operands[0].reg == X86_REG_RCX
        ):
            displacement = memory_displacement(instruction, base=X86_REG_RCX)
            if displacement is not None and index + 1 < len(instructions):
                target = direct_call_target(instructions[index + 1])
                if target is not None and resolver is None:
                    colony_reference_offset = displacement
                    resolver = target

        if resolver is not None and queue_handle_offset is None:
            displacement = memory_displacement(instruction, base=X86_REG_RAX)
            if (
                instruction.mnemonic == "mov"
                and displacement is not None
                and any(
                    operand.type == X86_OP_REG
                    and instruction.reg_name(operand.reg).startswith("e")
                    for operand in instruction.operands[:1]
                )
            ):
                queue_handle_offset = displacement

        target = rip_target(instruction)
        if (
            queue_registry_va is None
            and target is not None
            and instruction.mnemonic == "mov"
            and instruction.operands[0].type == X86_OP_REG
            and instruction.reg_name(instruction.operands[0].reg) == "rdx"
        ):
            queue_registry_va = target

        if instruction.mnemonic == "and" and any(
            operand.type == X86_OP_IMM and operand.imm == 0xFFFFFF
            for operand in instruction.operands
        ):
            mask_seen = True

        for operand in instruction.operands:
            if operand.type != X86_OP_MEM:
                continue
            item_offset_seen |= operand.mem.disp == 0x20
            count_offset_seen |= operand.mem.disp == expected_count_offset
            registry_bound_seen |= (
                instruction.mnemonic == "cmp"
                and instruction.reg_name(operand.mem.base) == "rdx"
                and operand.mem.disp == 0x20
            )
            registry_entries_seen |= (
                instruction.mnemonic == "mov"
                and instruction.reg_name(operand.mem.base) == "rdx"
                and operand.mem.disp == 0x18
            )
            registry_slot_seen |= (
                instruction.mnemonic == "mov"
                and operand.mem.index != 0
                and operand.mem.scale == 8
                and operand.mem.disp == 8
            )
            queue_identity_seen |= (
                instruction.mnemonic == "cmp" and operand.mem.disp == 8
            )
            if instruction.mnemonic == "call" and operand.mem.disp == 0xA0:
                rtti_calls += 1

        if instruction.mnemonic == "mov" and len(instruction.operands) == 2:
            destination, source = instruction.operands
            true_return_seen |= (
                destination.type == X86_OP_REG
                and destination.reg == X86_REG_AL
                and source.type == X86_OP_IMM
                and source.imm == 1
            )
        if instruction.mnemonic == "xor" and len(instruction.operands) == 2:
            register_ids = {
                operand.reg for operand in instruction.operands if operand.type == X86_OP_REG
            }
            false_return_seen |= len(register_ids) == 1 and register_ids <= {
                X86_REG_AL,
                X86_REG_EAX,
            }

    checks = {
        "resolver_after_colony_reference_load": resolver is not None,
        "queue_handle_load": queue_handle_offset is not None,
        "queue_registry_rip_load": queue_registry_va is not None,
        "handle_mask_0xffffff": mask_seen,
        "registry_bound_offset_0x20": registry_bound_seen,
        "registry_entries_offset_0x18": registry_entries_seen,
        "registry_slot_scale_and_offset": registry_slot_seen,
        "queue_identity_offset_0x08": queue_identity_seen,
        "queue_items_offset_0x20": item_offset_seen,
        "queue_count_offset_matches_progression": count_offset_seen,
        "two_rtti_vtable_0xa0_calls": rtti_calls >= 2,
        "boolean_true_and_false_returns": true_return_seen and false_return_seen,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ScanError("guard semantic validation failed: " + ", ".join(failed))

    return {
        "va": guard_va,
        "resolver_va": resolver,
        "queue_registry_va": queue_registry_va,
        "colony_reference_offset": colony_reference_offset,
        "queue_handle_offset": queue_handle_offset,
        "queue_item_handles_offset": 0x20,
        "queue_count_offset": expected_count_offset,
        "checks": checks,
    }


def locate_progression(image: PEImage) -> dict:
    section, relative = scan_pattern(image, PROGRESSION_PATTERN, "progression")
    va = image.image_base + section.virtual_address + relative
    code = image.bytes_at_va(va, len(PROGRESSION_PATTERN.values))
    instructions = list(make_disassembler().disasm(code, va))
    if len(instructions) < 12:
        raise ScanError("progression feature did not decode completely")

    count_offset = memory_displacement(instructions[0])
    capacity_offset = memory_displacement(instructions[5])
    count_pointer = instructions[0].operands[0]
    count_load = instructions[4].operands
    capacity_pointer = instructions[5].operands[0]
    comparison = instructions[6].operands
    selection = instructions[9].operands
    selected_load = instructions[10].operands
    checks = {
        "count_address_loaded": (
            instructions[0].mnemonic == "lea"
            and count_pointer.type == X86_OP_REG
            and count_offset is not None
        ),
        "count_loaded_through_pointer": (
            instructions[4].mnemonic == "mov"
            and len(count_load) == 2
            and count_load[1].type == X86_OP_MEM
            and count_load[1].mem.base == count_pointer.reg
        ),
        "capacity_address_loaded": (
            instructions[5].mnemonic == "lea"
            and capacity_pointer.type == X86_OP_REG
            and capacity_offset is not None
        ),
        "count_compared_with_capacity": (
            instructions[6].mnemonic == "cmp"
            and len(comparison) == 2
            and comparison[0].type == X86_OP_MEM
            and comparison[0].mem.base == capacity_pointer.reg
            and comparison[1].type == X86_OP_REG
            and comparison[1].reg == count_load[0].reg
        ),
        "signed_min_selected": (
            instructions[9].mnemonic == "cmovl"
            and len(selection) == 2
            and selection[0].type == X86_OP_REG
            and selection[0].reg == count_pointer.reg
            and selection[1].type == X86_OP_REG
            and selection[1].reg == capacity_pointer.reg
        ),
        "selected_count_loaded": (
            instructions[10].mnemonic == "mov"
            and len(selected_load) == 2
            and selected_load[1].type == X86_OP_MEM
            and selected_load[1].mem.base == count_pointer.reg
        ),
        "selected_count_decremented": instructions[11].mnemonic == "dec",
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ScanError("progression semantic validation failed: " + ", ".join(failed))
    return {
        "feature_va": va,
        "feature_file_offset": image.va_to_offset(va),
        "queue_count_offset": count_offset,
        "effective_capacity_offset": capacity_offset,
        "checks": checks,
    }


def zero_runs(data: bytes, minimum: int) -> Iterable[tuple[int, int]]:
    start = None
    for index, value in enumerate(data):
        if value == 0 and start is None:
            start = index
        if value != 0 and start is not None:
            if index - start >= minimum:
                yield start, index - start
            start = None
    if start is not None and len(data) - start >= minimum:
        yield start, len(data) - start


def find_code_cave(
    image: PEImage, minimum_size: int, call_va: int
) -> dict | None:
    candidates = []
    for section in image.executable_sections():
        if section.raw_size <= section.virtual_size:
            continue
        tail_start = section.virtual_size
        tail = image.data[
            section.raw_offset + tail_start : section.raw_offset + section.raw_size
        ]
        for relative, length in zero_runs(tail, minimum_size):
            raw_relative = tail_start + relative
            aligned_relative = (raw_relative + 0xF) & ~0xF
            adjustment = aligned_relative - raw_relative
            available = length - adjustment
            if available < minimum_size:
                continue
            va = image.image_base + section.virtual_address + aligned_relative
            if not -(1 << 31) <= va - (call_va + 5) < (1 << 31):
                continue
            candidates.append(
                {
                    "section": section.name,
                    "va": va,
                    "rva": va - image.image_base,
                    "file_offset": section.raw_offset + aligned_relative,
                    "available_bytes": available,
                    "source": "zero-filled executable raw tail",
                }
            )
    if not candidates:
        return None
    if len(candidates) != 1:
        details = ", ".join(
            f"{candidate['section']}@0x{candidate['va']:X}/0x{candidate['available_bytes']:X}"
            for candidate in candidates[:10]
        )
        raise ScanError(
            f"executable code-cave search produced {len(candidates)} candidates"
            + (f": {details}" if details else "")
        )
    return candidates[0]


def plan_new_executable_section(image: PEImage, minimum_size: int) -> dict:
    """Reserve an aligned RX PE section when no reviewed code cave exists."""
    if any(section.name == ".bca" for section in image.sections):
        raise ScanError("target already contains a .bca section")
    if not image.sections:
        raise ScanError("PE image has no sections")

    header_offset = image.section_table_offset + image.section_count * 40
    header_end = header_offset + 40
    first_raw_offset = min(section.raw_offset for section in image.sections)
    if header_end > image.size_of_headers or header_end > first_raw_offset:
        raise ScanError("PE header has no room for an additional section entry")
    expected_header = image.data[header_offset:header_end]
    if len(expected_header) != 40 or any(expected_header):
        raise ScanError("next PE section header slot is not zero-filled")

    virtual_size = max(0x80, minimum_size)
    raw_size = align_up(virtual_size, image.file_alignment)
    last_rva = max(
        section.virtual_address + max(section.virtual_size, section.raw_size)
        for section in image.sections
    )
    virtual_address = align_up(last_rva, image.section_alignment)
    raw_offset = align_up(len(image.data), image.file_alignment)
    size_of_image = align_up(virtual_address + virtual_size, image.section_alignment)
    if size_of_image <= image.size_of_image:
        raise ScanError("new section does not extend the PE image")
    if image.size_of_code > 0xFFFFFFFF - raw_size:
        raise ScanError("PE SizeOfCode would overflow")

    characteristics = 0x60000020  # code, executable, readable
    section_header = struct.pack(
        "<8sIIIIIIHHI",
        b".bca\0\0\0\0",
        virtual_size,
        virtual_address,
        raw_size,
        raw_offset,
        0,
        0,
        0,
        0,
        characteristics,
    )
    return {
        "section": ".bca",
        "va": image.image_base + virtual_address,
        "rva": virtual_address,
        "file_offset": raw_offset,
        "available_bytes": raw_size,
        "source": "new executable PE section",
        "section_header_offset": header_offset,
        "section_header_expected": expected_header,
        "section_header": section_header,
        "original_section_count": image.section_count,
        "new_section_count": image.section_count + 1,
        "coff_section_count_offset": image.coff_offset + 2,
        "original_size_of_code": image.size_of_code,
        "new_size_of_code": image.size_of_code + raw_size,
        "size_of_code_offset": image.optional_offset + 4,
        "original_size_of_image": image.size_of_image,
        "new_size_of_image": size_of_image,
        "size_of_image_offset": image.optional_offset + 56,
        "original_file_size": len(image.data),
        "raw_size": raw_size,
        "virtual_size": virtual_size,
        "characteristics": characteristics,
    }


def build_helper(
    helper_va: int,
    resolver_va: int,
    queue_registry_va: int,
    colony_reference_offset: int,
    queue_handle_offset: int,
    count_offset: int,
    capacity_offset: int,
) -> bytes:
    for label, value in (
        ("colony reference", colony_reference_offset),
        ("queue handle", queue_handle_offset),
    ):
        if not -(1 << 31) <= value < (1 << 31):
            raise ScanError(f"{label} offset does not fit disp32")
    for label, value in (("count", count_offset), ("capacity", capacity_offset)):
        if not -128 <= value <= 127:
            raise ScanError(f"{label} offset does not fit the validated helper encoding")

    payload = bytearray.fromhex(
        "48 83 EC 28"
        "48 8B 89 00 00 00 00"
        "E8 00 00 00 00"
        "8B 80 00 00 00 00"
        "48 8B 15 00 00 00 00"
        "48 85 D2 74 38"
        "41 89 C0 41 81 E0 FF FF FF 00"
        "44 3B 42 20 73 28"
        "48 8B 52 18 45 89 C1 49 C1 E1 04"
        "4A 8B 54 0A 08 48 85 D2 74 13"
        "39 42 08 75 0E"
        "8B 4A 00 3B 4A 00 0F 9D C0"
        "48 83 C4 28 C3"
        "31 C0 48 83 C4 28 C3"
    )
    struct.pack_into("<i", payload, 7, colony_reference_offset)
    call_next = helper_va + 16
    resolver_displacement = resolver_va - call_next
    if not -(1 << 31) <= resolver_displacement < (1 << 31):
        raise ScanError("resolver is outside CALL rel32 range")
    struct.pack_into("<i", payload, 12, resolver_displacement)
    struct.pack_into("<i", payload, 18, queue_handle_offset)
    registry_next = helper_va + 29
    registry_displacement = queue_registry_va - registry_next
    if not -(1 << 31) <= registry_displacement < (1 << 31):
        raise ScanError("queue registry is outside RIP-relative disp32 range")
    struct.pack_into("<i", payload, 25, registry_displacement)
    payload[78] = count_offset & 0xFF
    payload[81] = capacity_offset & 0xFF
    return bytes(payload)


def validate_position_independent_helper(
    payload: bytes, helper_va: int, image_base: int, size_of_image: int
) -> None:
    image_end = image_base + size_of_image
    instructions = list(make_disassembler().disasm(payload, helper_va))
    if sum(instruction.size for instruction in instructions) != len(payload):
        raise ScanError("helper does not decode as a complete instruction stream")
    for instruction in instructions:
        for operand in instruction.operands:
            if operand.type == X86_OP_MEM:
                absolute = operand.mem.base == 0 and operand.mem.index == 0
                if absolute and image_base <= operand.mem.disp < image_end:
                    raise ScanError(
                        f"helper contains an unrelocated absolute memory operand "
                        f"at +0x{instruction.address - helper_va:X}"
                    )
            if (
                instruction.mnemonic in {"mov", "movabs"}
                and operand.type == X86_OP_IMM
                and image_base <= operand.imm < image_end
            ):
                raise ScanError(
                    f"helper contains an unrelocated image-address immediate "
                    f"at +0x{instruction.address - helper_va:X}"
                )


def hex_bytes(data: bytes) -> str:
    return " ".join(f"{value:02X}" for value in data)


def as_hex(value):
    if isinstance(value, bytes):
        return hex_bytes(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return f"0x{value:X}"
    if isinstance(value, dict):
        return {key: as_hex(item) for key, item in value.items()}
    if isinstance(value, list):
        return [as_hex(item) for item in value]
    return value


def build_plan(path: Path) -> dict:
    image = PEImage(path)
    scheduler = locate_scheduler(image)
    progression = locate_progression(image)
    guard = validate_guard(
        image,
        scheduler["guard_va"],
        progression["queue_count_offset"],
    )
    if guard["queue_count_offset"] != progression["queue_count_offset"]:
        raise ScanError("guard and progression disagree on the queue count offset")

    provisional_payload_size = 0x61
    cave = find_code_cave(
        image, max(0x80, provisional_payload_size), scheduler["call_va"]
    )
    if cave is None:
        cave = plan_new_executable_section(image, provisional_payload_size)
    helper = build_helper(
        helper_va=cave["va"],
        resolver_va=guard["resolver_va"],
        queue_registry_va=guard["queue_registry_va"],
        colony_reference_offset=guard["colony_reference_offset"],
        queue_handle_offset=guard["queue_handle_offset"],
        count_offset=progression["queue_count_offset"],
        capacity_offset=progression["effective_capacity_offset"],
    )
    if len(helper) != provisional_payload_size:
        raise ScanError("internal helper size invariant failed")
    validate_position_independent_helper(
        helper,
        cave["va"],
        image.image_base,
        cave.get("new_size_of_image", image.size_of_image),
    )

    call_displacement = cave["va"] - (scheduler["call_va"] + 5)
    replacement_call = b"\xE8" + struct.pack("<i", call_displacement)
    checks = {
        "scheduler_signature_unique": True,
        "guard_semantics_validated": True,
        "progression_signature_unique": True,
        "count_offset_agrees": True,
        "injection_site_validated": True,
        "replacement_call_is_rel32": True,
        "helper_is_position_independent": True,
        "scanner_is_read_only": True,
    }
    target_sha256 = hashlib.sha256(image.data).hexdigest().upper()
    return {
        "schema_version": "1.1",
        "mode": "scan-only",
        "target": {
            "path": str(path.resolve()),
            "size": len(image.data),
            "image_base": image.image_base,
            "size_of_image": image.size_of_image,
            "md5": hashlib.md5(image.data).hexdigest().upper(),
            "sha256": target_sha256,
            "known_profile": KNOWN_PROFILES.get(target_sha256),
        },
        "scheduler": scheduler,
        "original_guard": guard,
        "native_progression": progression,
        "helper": {
            **cave,
            "payload_bytes": len(helper),
            "payload_sha256": hashlib.sha256(helper).hexdigest().upper(),
            "payload": helper,
        },
        "call_patch": {
            "va": scheduler["call_va"],
            "rva": scheduler["call_rva"],
            "file_offset": scheduler["call_file_offset"],
            "expected_bytes": scheduler["call_bytes"],
            "replacement_bytes": replacement_call,
            "original_target": scheduler["guard_va"],
            "replacement_target": cave["va"],
        },
        "checks": checks,
    }


def validate_added_section(image: PEImage, helper: dict) -> None:
    if helper.get("source") != "new executable PE section":
        return
    if image.section_count != helper["new_section_count"]:
        raise ScanError("patched PE section count does not match the plan")
    if image.size_of_image != helper["new_size_of_image"]:
        raise ScanError("patched PE image size does not match the plan")
    section = image.sections[-1]
    expected = (
        helper["section"],
        helper["rva"],
        helper["virtual_size"],
        helper["file_offset"],
        helper["raw_size"],
        helper["characteristics"],
    )
    actual = (
        section.name,
        section.virtual_address,
        section.virtual_size,
        section.raw_offset,
        section.raw_size,
        section.characteristics,
    )
    if actual != expected:
        raise ScanError("patched .bca section does not match the plan")


def build_patched_image(source: bytes, plan: dict) -> bytes:
    expected_hash = plan["target"]["sha256"]
    actual_hash = hashlib.sha256(source).hexdigest().upper()
    if actual_hash != expected_hash:
        raise ScanError("source changed after scanning")

    call = plan["call_patch"]
    call_offset = call["file_offset"]
    expected_call = call["expected_bytes"]
    if source[call_offset : call_offset + len(expected_call)] != expected_call:
        raise ScanError("call-site bytes changed after scanning")

    helper = plan["helper"]
    cave_offset = helper["file_offset"]
    available = helper["available_bytes"]
    if len(helper["payload"]) > available:
        raise ScanError("helper payload no longer fits in the injection site")

    if helper.get("source") == "new executable PE section":
        if len(source) != helper["original_file_size"]:
            raise ScanError("source file size changed after scanning")
        header_offset = helper["section_header_offset"]
        header_expected = helper["section_header_expected"]
        if source[header_offset : header_offset + len(header_expected)] != header_expected:
            raise ScanError("PE section header slot changed after scanning")
        if u16(source, helper["coff_section_count_offset"]) != helper[
            "original_section_count"
        ]:
            raise ScanError("PE section count changed after scanning")
        if u32(source, helper["size_of_code_offset"]) != helper["original_size_of_code"]:
            raise ScanError("PE SizeOfCode changed after scanning")
        if u32(source, helper["size_of_image_offset"]) != helper[
            "original_size_of_image"
        ]:
            raise ScanError("PE SizeOfImage changed after scanning")
        if cave_offset < len(source):
            raise ScanError("new PE section raw data would overlap the source file")

        patched = bytearray(source)
        patched.extend(b"\0" * (cave_offset - len(patched)))
        patched.extend(b"\0" * helper["raw_size"])
        patched[header_offset : header_offset + 40] = helper["section_header"]
        struct.pack_into(
            "<H", patched, helper["coff_section_count_offset"], helper["new_section_count"]
        )
        struct.pack_into(
            "<I", patched, helper["size_of_code_offset"], helper["new_size_of_code"]
        )
        struct.pack_into(
            "<I", patched, helper["size_of_image_offset"], helper["new_size_of_image"]
        )
    else:
        patched = bytearray(source)

    if any(patched[cave_offset : cave_offset + available]):
        raise ScanError("injection site is no longer entirely zero-filled")

    call_end = call_offset + len(call["replacement_bytes"])
    helper_end = cave_offset + len(helper["payload"])
    if max(call_offset, cave_offset) < min(call_end, helper_end):
        raise ScanError("call patch and helper payload overlap")

    patched[cave_offset:helper_end] = helper["payload"]
    patched[call_offset:call_end] = call["replacement_bytes"]
    return bytes(patched)


def apply_plan(path: Path, plan: dict, backup_path: Path | None = None) -> dict:
    source = path.read_bytes()
    patched = build_patched_image(source, plan)
    original_sha256 = hashlib.sha256(source).hexdigest().upper()
    patched_sha256 = hashlib.sha256(patched).hexdigest().upper()
    if backup_path is None:
        backup_path = path.with_name(
            f"{path.name}.bca-backup-{original_sha256[:16]}"
        )
    backup_path = backup_path.resolve()
    if backup_path == path.resolve():
        raise ScanError("backup path must differ from the executable")

    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.bca-patch-",
            suffix=".tmp",
            dir=path.parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as output:
            output.write(patched)
            output.flush()
            os.fsync(output.fileno())
        shutil.copystat(path, temporary_path)
        if temporary_path.read_bytes() != patched:
            raise ScanError("temporary patched image verification failed")
        if plan["helper"].get("source") == "new executable PE section":
            validate_added_section(PEImage(temporary_path), plan["helper"])

        if backup_path.exists():
            backup_hash = hashlib.sha256(backup_path.read_bytes()).hexdigest().upper()
            if backup_hash != original_sha256:
                raise ScanError(
                    f"backup already exists with different contents: {backup_path}"
                )
        else:
            shutil.copy2(path, backup_path)
            backup_hash = hashlib.sha256(backup_path.read_bytes()).hexdigest().upper()
            if backup_hash != original_sha256:
                raise ScanError("automatic backup verification failed")

        os.replace(temporary_path, path)
        temporary_path = None
        if hashlib.sha256(path.read_bytes()).hexdigest().upper() != patched_sha256:
            raise ScanError("final executable verification failed")
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    return {
        "status": "applied",
        "executable": str(path.resolve()),
        "backup": str(backup_path),
        "original_sha256": original_sha256,
        "patched_sha256": patched_sha256,
        "call_patch": as_hex(plan["call_patch"]),
        "helper": {
            "va": f"0x{plan['helper']['va']:X}",
            "file_offset": f"0x{plan['helper']['file_offset']:X}",
            "payload_bytes": len(plan["helper"]["payload"]),
            "payload_sha256": plan["helper"]["payload_sha256"],
        },
    }


def restore_backup(
    path: Path, backup_path: Path, plan: dict | None = None
) -> dict:
    path = path.resolve()
    backup_path = backup_path.resolve()
    if path == backup_path:
        raise ScanError("backup path must differ from the executable")
    if plan is None:
        plan = build_plan(backup_path)

    original = backup_path.read_bytes()
    current = path.read_bytes()
    expected_patched = build_patched_image(original, plan)
    if current != expected_patched:
        raise ScanError(
            "current executable is not the exact patch derived from this backup"
        )

    patched_sha256 = hashlib.sha256(current).hexdigest().upper()
    original_sha256 = hashlib.sha256(original).hexdigest().upper()
    recovery_path = path.with_name(
        f"{path.name}.bca-patched-{patched_sha256[:16]}"
    )
    if recovery_path.exists():
        if recovery_path.read_bytes() != current:
            raise ScanError(
                f"patched recovery file exists with different contents: {recovery_path}"
            )
    else:
        shutil.copy2(path, recovery_path)
        if recovery_path.read_bytes() != current:
            raise ScanError("patched recovery-file verification failed")

    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.bca-restore-",
            suffix=".tmp",
            dir=path.parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as output:
            output.write(original)
            output.flush()
            os.fsync(output.fileno())
        shutil.copystat(backup_path, temporary_path)
        if temporary_path.read_bytes() != original:
            raise ScanError("temporary restored image verification failed")
        os.replace(temporary_path, path)
        temporary_path = None
        if path.read_bytes() != original:
            raise ScanError("final restored executable verification failed")
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    return {
        "status": "restored",
        "executable": str(path),
        "source_backup": str(backup_path),
        "patched_recovery": str(recovery_path),
        "restored_sha256": original_sha256,
        "previous_patched_sha256": patched_sha256,
    }


def parse_steam_library_paths(text: str) -> list[Path]:
    paths = []
    for match in STEAM_LIBRARY_PATH_RE.finditer(text):
        raw_path = match.group("path").replace("\\\\", "\\")
        paths.append(Path(raw_path))
    return paths


def steam_install_roots() -> list[Path]:
    roots: list[Path] = []
    explicit_executable = os.environ.get("STELLARIS_EXE")
    if explicit_executable:
        roots.append(Path(explicit_executable).expanduser().resolve().parents[3])

    if sys.platform == "win32":
        try:
            import winreg

            registry_locations = (
                (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                (
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\WOW6432Node\Valve\Steam",
                ),
            )
            for hive, key_name in registry_locations:
                try:
                    with winreg.OpenKey(hive, key_name) as key:
                        for value_name in ("SteamPath", "InstallPath"):
                            try:
                                value, _ = winreg.QueryValueEx(key, value_name)
                                roots.append(Path(value))
                            except FileNotFoundError:
                                continue
                except FileNotFoundError:
                    continue
        except ImportError:
            pass

    for environment_name in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(environment_name)
        if base:
            roots.append(Path(base) / "Steam")

    discovered = []
    seen = set()
    for root in roots:
        root = root.expanduser()
        key = str(root).casefold()
        if key in seen:
            continue
        seen.add(key)
        discovered.append(root)
        library_file = root / "steamapps" / "libraryfolders.vdf"
        if library_file.is_file():
            try:
                discovered.extend(
                    parse_steam_library_paths(
                        library_file.read_text(encoding="utf-8-sig")
                    )
                )
            except OSError:
                continue
    return discovered


def discover_stellaris_executables() -> list[Path]:
    explicit = os.environ.get("STELLARIS_EXE")
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    for root in steam_install_roots():
        candidates.append(root / "steamapps" / "common" / "Stellaris" / "stellaris.exe")

    found = []
    seen = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        key = str(resolved).casefold()
        if key in seen or not resolved.is_file():
            continue
        seen.add(key)
        found.append(resolved)
    return found


def resolve_executable(explicit: Path | None, auto: bool, prompt: bool) -> Path:
    selected_modes = int(explicit is not None) + int(auto) + int(prompt)
    if selected_modes > 1:
        raise ScanError(
            "provide one of an executable path, --auto, or --prompt"
        )
    if explicit is not None:
        return explicit.expanduser().resolve()
    candidates = discover_stellaris_executables()
    if prompt:
        default = candidates[0] if len(candidates) == 1 else None
        if candidates:
            print("Detected Stellaris executable(s):")
            for candidate in candidates:
                print(f"  {candidate}")
        else:
            print("No Stellaris executable was detected automatically.")
        suffix = f" [{default}]" if default else ""
        entered = input(f"Enter the full path to stellaris.exe{suffix}: ").strip()
        if entered:
            return Path(entered.strip('"')).expanduser().resolve()
        if default is not None:
            return default
        raise ScanError("no executable path was entered")
    if not auto:
        raise ScanError("an executable path, --auto, or --prompt is required")
    if len(candidates) != 1:
        details = ", ".join(str(path) for path in candidates)
        raise ScanError(
            f"automatic Stellaris discovery found {len(candidates)} installations"
            + (f": {details}" if details else "")
            + "; pass the executable path explicitly"
        )
    return candidates[0]


def find_matching_backup(path: Path) -> tuple[Path, dict]:
    current = path.read_bytes()
    matches = []
    for backup in sorted(path.parent.glob(f"{path.name}.bca-backup-*")):
        try:
            plan = build_plan(backup)
            if build_patched_image(backup.read_bytes(), plan) == current:
                matches.append((backup, plan))
        except (OSError, ScanError, struct.error, ValueError):
            continue
    if len(matches) != 1:
        raise ScanError(
            f"automatic restore found {len(matches)} backups matching the current patch"
        )
    return matches[0]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only feature scanner for the automation queue-capacity patch"
    )
    parser.add_argument(
        "executable",
        nargs="?",
        type=Path,
        help="path to stellaris.exe",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="locate Stellaris through the Steam installation and library files",
    )
    parser.add_argument(
        "--prompt",
        action="store_true",
        help="show detected installations and prompt for the stellaris.exe path",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="create a verified backup and atomically apply the generated plan",
    )
    mode.add_argument(
        "--restore-backup",
        type=Path,
        help="restore an exact matching automatic backup and retain the patched image",
    )
    mode.add_argument(
        "--restore-auto-backup",
        action="store_true",
        help="find the one backup that exactly reconstructs the current patch and restore it",
    )
    parser.add_argument(
        "--backup",
        type=Path,
        help="backup path for --apply (default: hash-suffixed sibling file)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the JSON plan to this path instead of standard output",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        executable = resolve_executable(args.executable, args.auto, args.prompt)
        if args.backup and not args.apply:
            raise ScanError("--backup is only valid with --apply")
        if args.restore_auto_backup:
            backup_path, backup_plan = find_matching_backup(executable)
            result = restore_backup(executable, backup_path, backup_plan)
        elif args.restore_backup:
            result = restore_backup(executable, args.restore_backup)
        else:
            raw_plan = build_plan(executable)
            result = (
                apply_plan(executable, raw_plan, args.backup)
                if args.apply
                else as_hex(raw_plan)
            )
    except (OSError, ScanError, struct.error, ValueError) as error:
        print(f"operation refused: {error}", file=sys.stderr)
        return 2
    rendered = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
