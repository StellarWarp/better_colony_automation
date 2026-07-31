"""Capture the native colony-automation queue guard and resolved queue state."""

from __future__ import annotations

import argparse
from pathlib import Path
import struct

from pybag import DbgEng, UserDbg

from debug_stellaris_session import detach_session, go_or_timeout


AUTOMATION_GUARD_CALL_OFFSET = 0xEE7081
QUEUE_REGISTRY_OFFSET = 0x32876D8
QUEUE_ITEM_REGISTRY_OFFSET = 0x32876C8


def read_u32(debugger: UserDbg, address: int) -> int:
    return struct.unpack("<I", debugger.read(address, 4))[0]


def read_u64(debugger: UserDbg, address: int) -> int:
    return struct.unpack("<Q", debugger.read(address, 8))[0]


def module_base(debugger: UserDbg, module_name: str) -> int:
    def normalize(value: str | bytes) -> str:
        if isinstance(value, bytes):
            return value.decode(errors="replace").lower()
        return value.lower()

    wanted = module_name.lower()
    for names, parameters in debugger.mod.modules():
        image_name = normalize(names[1])
        module = normalize(names[0])
        if wanted in (image_name, module):
            return parameters.Base
    raise RuntimeError(f"Module not found: {module_name}")


def append_registers(output, debugger: UserDbg, names: tuple[str, ...]) -> None:
    for name in names:
        try:
            output.write(f"{name} = 0x{debugger.reg[name]:016X}\n")
        except Exception as error:
            output.write(f"{name} = <failed: {error!r}>\n")


def resolve_handle(
    debugger: UserDbg, registry_address: int, handle: int, id_offset: int
) -> int:
    registry = read_u64(debugger, registry_address)
    index = handle & 0xFFFFFF
    maximum = read_u32(debugger, registry + 0x20)
    if index >= maximum:
        return 0
    entries = read_u64(debugger, registry + 0x18)
    candidate = read_u64(debugger, entries + 8 + index * 0x10)
    if candidate == 0 or read_u32(debugger, candidate + id_offset) != handle:
        return 0
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("report", type=Path)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    args.report.parent.mkdir(parents=True, exist_ok=True)
    debugger = UserDbg()
    breakpoint = None
    attached = False

    try:
        debugger.attach(args.pid, initial_break=True)
        attached = True
        base = module_base(debugger, "stellaris")
        breakpoint = debugger.breakpoints.set(
            base + AUTOMATION_GUARD_CALL_OFFSET, oneshot=True
        )
        go_or_timeout(debugger, args.timeout)
        breakpoint = None

        with args.report.open("w", encoding="ascii", errors="replace") as output:
            output.write("status: automation queue guard call captured\n")
            output.write(f"pid: {debugger.pid}\n")
            output.write(f"stellaris_base: 0x{base:016X}\n")
            output.write(f"pc: 0x{debugger.reg.get_pc():016X}\n\n")
            append_registers(
                output, debugger, ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9")
            )
            colony = debugger.reg["rcx"]
            output.write(f"\ncolony: 0x{colony:016X}\n")
            output.write(
                f"colony+0xf78: 0x{read_u64(debugger, colony + 0xF78):016X}\n"
            )
            output.write("\ncallsite disassembly:\n")
            output.write(str(debugger.disasm(debugger.reg.get_pc() - 0x20, 24)))
            output.write("\n")

            debugger.stepi()
            output.write(f"\nguard entry pc: 0x{debugger.reg.get_pc():016X}\n")
            output.write(str(debugger.disasm(debugger.reg.get_pc(), 24)))
            output.write("\n")

            for _ in range(24):
                instruction = str(debugger.instruction_at()).lower()
                if "call" in instruction:
                    debugger.stepo()
                    break
                debugger.stepi()
            else:
                raise RuntimeError("First guard call was not reached")

            planet_reference = debugger.reg["rax"]
            output.write(
                f"\nafter FUN_140d464b0 pc: 0x{debugger.reg.get_pc():016X}\n"
            )
            output.write(f"resolved_planet_reference: 0x{planet_reference:016X}\n")
            queue_handle = read_u32(debugger, planet_reference + 0xC4)
            output.write(f"queue_handle: 0x{queue_handle:08X}\n")
            queue = resolve_handle(
                debugger, base + QUEUE_REGISTRY_OFFSET, queue_handle, 0x8
            )
            output.write(f"queue: 0x{queue:016X}\n")
            if queue:
                count = read_u32(debugger, queue + 0x2C)
                handles = read_u64(debugger, queue + 0x20)
                output.write(f"queue_count: {count}\n")
                output.write(f"queue_handles: 0x{handles:016X}\n")
                queue_values = [
                    read_u64(debugger, queue + offset)
                    for offset in range(0, 0x80, 8)
                ]
                output.write(
                    "queue_qwords_00_78: " +
                    " ".join(f"{value:016X}" for value in queue_values) +
                    "\n"
                )
                for index in range(min(count, 64)):
                    handle = read_u32(debugger, handles + index * 4)
                    item = resolve_handle(
                        debugger, base + QUEUE_ITEM_REGISTRY_OFFSET, handle, 0x8
                    )
                    output.write(
                        f"item[{index}] handle=0x{handle:08X} "
                        f"object=0x{item:016X}"
                    )
                    if item:
                        output.write(
                            f" type=0x{read_u64(debugger, item + 0x18):016X}"
                            f" field_28={read_u64(debugger, item + 0x28)}"
                        )
                    output.write("\n")
                    if item:
                        values = [
                            read_u64(debugger, item + offset)
                            for offset in range(0, 0x80, 8)
                        ]
                        output.write(
                            "  qwords_00_78: " +
                            " ".join(f"{value:016X}" for value in values) +
                            "\n"
                        )
    finally:
        if attached:
            if breakpoint is not None:
                try:
                    debugger.breakpoints.remove(breakpoint)
                except Exception:
                    pass
            detach_session(debugger)
        debugger.Release()


if __name__ == "__main__":
    main()
