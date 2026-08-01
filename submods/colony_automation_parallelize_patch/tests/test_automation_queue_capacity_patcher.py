import importlib.util
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "automation_queue_capacity_patcher.py"
)
SPEC = importlib.util.spec_from_file_location("automation_queue_capacity_patcher", MODULE_PATH)
patcher = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = patcher
SPEC.loader.exec_module(patcher)


class BytePatternTests(unittest.TestCase):
    def test_wildcards_match_only_variable_bytes(self):
        pattern = patcher.BytePattern.parse("49 8B ?? 08")
        self.assertEqual(pattern.find_all(bytes.fromhex("00 49 8B 4D 08 49 8B 4D 09")), [1])

    def test_empty_pattern_has_no_matches(self):
        self.assertEqual(patcher.BytePattern.parse("").find_all(b"abc"), [])

    def test_scheduler_anchor_does_not_depend_on_colony_register(self):
        r13 = bytes.fromhex(
            "E8 00 00 00 00 84 C0 0F 85 00 00 00 00 41 83 7D 24 00 0F 84 00 00 00 00"
        )
        r15 = bytes.fromhex(
            "E8 00 00 00 00 84 C0 0F 85 00 00 00 00 41 83 7F 24 00 0F 84 00 00 00 00"
        )
        self.assertEqual(patcher.SCHEDULER_ANCHOR_PATTERN.find_all(r13), [0])
        self.assertEqual(patcher.SCHEDULER_ANCHOR_PATTERN.find_all(r15), [0])

    def test_steam_library_paths_support_escaped_backslashes(self):
        text = (
            '"0" { "path" "C:\\\\Program Files (x86)\\\\Steam" }\n'
            '"1" { "path" "D:\\\\SteamLibrary" }\n'
        )
        self.assertEqual(
            patcher.parse_steam_library_paths(text),
            [
                Path(r"C:\Program Files (x86)\Steam"),
                Path(r"D:\SteamLibrary"),
            ],
        )

    def test_prompt_uses_unique_detected_path_on_empty_input(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory, "stellaris.exe")
            executable.write_bytes(b"MZ")
            with (
                patch.object(
                    patcher,
                    "discover_stellaris_executables",
                    return_value=[executable],
                ),
                patch("builtins.input", return_value=""),
            ):
                self.assertEqual(
                    patcher.resolve_executable(None, False, True),
                    executable.resolve(),
                )

    def test_prompt_accepts_quoted_explicit_path(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory, "custom", "stellaris.exe")
            with (
                patch.object(
                    patcher,
                    "discover_stellaris_executables",
                    return_value=[],
                ),
                patch("builtins.input", return_value=f'"{executable}"'),
            ):
                self.assertEqual(
                    patcher.resolve_executable(None, False, True),
                    executable.resolve(),
                )


class HelperEncodingTests(unittest.TestCase):
    def test_current_profile_reproduces_reviewed_payload(self):
        payload = patcher.build_helper(
            helper_va=0x1423B4700,
            resolver_va=0x140D464B0,
            queue_registry_va=0x1432876D8,
            colony_reference_offset=0xF78,
            queue_handle_offset=0xC4,
            count_offset=0x2C,
            capacity_offset=0x48,
        )
        reviewed = MODULE_PATH.with_name("automation_queue_capacity_guard.bin").read_bytes()
        self.assertEqual(payload, reviewed)

    def test_helper_targets_survive_aslr_rebase(self):
        preferred = 0x140000000
        runtime = 0x7FF6C8650000
        helper_va = 0x1423B4700
        resolver_va = 0x140D464B0
        registry_va = 0x1432876D8
        payload = patcher.build_helper(
            helper_va=helper_va,
            resolver_va=resolver_va,
            queue_registry_va=registry_va,
            colony_reference_offset=0xF78,
            queue_handle_offset=0xC4,
            count_offset=0x2C,
            capacity_offset=0x48,
        )
        call_displacement = struct.unpack_from("<i", payload, 12)[0]
        registry_displacement = struct.unpack_from("<i", payload, 25)[0]
        runtime_helper = runtime + helper_va - preferred
        self.assertEqual(
            runtime_helper + 16 + call_displacement,
            runtime + resolver_va - preferred,
        )
        self.assertEqual(
            runtime_helper + 29 + registry_displacement,
            runtime + registry_va - preferred,
        )
        patcher.validate_position_independent_helper(
            payload,
            helper_va,
            preferred,
            0x3950000,
        )

    def test_absolute_image_address_is_rejected(self):
        failed_payload = bytes.fromhex(
            "49 BA D8 76 28 43 01 00 00 00"
            "49 8B 12"
        )
        with self.assertRaisesRegex(
            patcher.ScanError, "unrelocated image-address immediate"
        ):
            patcher.validate_position_independent_helper(
                failed_payload,
                0x1423B4700,
                0x140000000,
                0x3950000,
            )

    def test_patch_builder_changes_only_declared_regions(self):
        source = bytes(128)
        source_hash = patcher.hashlib.sha256(source).hexdigest().upper()
        plan = {
            "target": {"sha256": source_hash},
            "call_patch": {
                "file_offset": 8,
                "expected_bytes": bytes(5),
                "replacement_bytes": b"\xE8\x01\x02\x03\x04",
            },
            "helper": {
                "file_offset": 64,
                "available_bytes": 32,
                "payload": b"\x90\xC3",
            },
        }
        patched = patcher.build_patched_image(source, plan)
        self.assertEqual(patched[8:13], b"\xE8\x01\x02\x03\x04")
        self.assertEqual(patched[64:66], b"\x90\xC3")
        self.assertEqual(patched[13:64], source[13:64])

    def test_patch_builder_rejects_nonzero_cave(self):
        source = bytearray(128)
        source[70] = 1
        source = bytes(source)
        plan = {
            "target": {"sha256": patcher.hashlib.sha256(source).hexdigest().upper()},
            "call_patch": {
                "file_offset": 8,
                "expected_bytes": bytes(5),
                "replacement_bytes": b"\xE8\x01\x02\x03\x04",
            },
            "helper": {
                "file_offset": 64,
                "available_bytes": 32,
                "payload": b"\x90\xC3",
            },
        }
        with self.assertRaisesRegex(patcher.ScanError, "no longer entirely zero"):
            patcher.build_patched_image(source, plan)

    def test_apply_plan_creates_verified_backup_and_replaces_target(self):
        source = bytes(128)
        source_hash = patcher.hashlib.sha256(source).hexdigest().upper()
        payload = b"\x90\xC3"
        plan = {
            "target": {"sha256": source_hash},
            "call_patch": {
                "va": 0x140001000,
                "rva": 0x1000,
                "file_offset": 8,
                "expected_bytes": bytes(5),
                "replacement_bytes": b"\xE8\x01\x02\x03\x04",
                "original_target": 0x140002000,
                "replacement_target": 0x140003000,
            },
            "helper": {
                "va": 0x140003000,
                "file_offset": 64,
                "available_bytes": 32,
                "payload": payload,
                "payload_sha256": patcher.hashlib.sha256(payload).hexdigest().upper(),
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "game.exe")
            target.write_bytes(source)
            receipt = patcher.apply_plan(target, plan)
            backup = Path(receipt["backup"])
            self.assertEqual(backup.read_bytes(), source)
            self.assertEqual(
                target.read_bytes(),
                patcher.build_patched_image(source, plan),
            )
            self.assertEqual(receipt["status"], "applied")
            restore = patcher.restore_backup(target, backup, plan)
            self.assertEqual(target.read_bytes(), source)
            self.assertEqual(
                Path(restore["patched_recovery"]).read_bytes(),
                patcher.build_patched_image(source, plan),
            )
            self.assertEqual(restore["status"], "restored")


class MinimalPEParserTests(unittest.TestCase):
    @staticmethod
    def make_minimal_pe() -> bytearray:
        image = bytearray(0x600)
        image[:2] = b"MZ"
        struct.pack_into("<I", image, 0x3C, 0x80)
        image[0x80:0x84] = b"PE\0\0"
        coff = 0x84
        struct.pack_into("<H", image, coff, 0x8664)
        struct.pack_into("<H", image, coff + 2, 1)
        struct.pack_into("<H", image, coff + 16, 0xF0)
        optional = coff + 20
        struct.pack_into("<H", image, optional, 0x20B)
        struct.pack_into("<I", image, optional + 4, 0x200)
        struct.pack_into("<Q", image, optional + 24, 0x140000000)
        struct.pack_into("<I", image, optional + 32, 0x1000)
        struct.pack_into("<I", image, optional + 36, 0x200)
        struct.pack_into("<I", image, optional + 56, 0x2000)
        struct.pack_into("<I", image, optional + 60, 0x400)
        section = optional + 0xF0
        image[section : section + 8] = b".text\0\0\0"
        struct.pack_into("<I", image, section + 8, 0x200)
        struct.pack_into("<I", image, section + 12, 0x1000)
        struct.pack_into("<I", image, section + 16, 0x200)
        struct.pack_into("<I", image, section + 20, 0x400)
        struct.pack_into("<I", image, section + 36, 0x60000020)
        return image

    def test_rva_and_file_offset_conversion(self):
        image = self.make_minimal_pe()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "minimal.exe")
            path.write_bytes(image)
            parsed = patcher.PEImage(path)

        self.assertEqual(parsed.rva_to_offset(0x1010), 0x410)
        self.assertEqual(parsed.offset_to_rva(0x410), 0x1010)
        self.assertEqual([section.name for section in parsed.executable_sections()], [".text"])

    def test_new_section_plan_extends_and_remains_parseable(self):
        source = bytes(self.make_minimal_pe())
        with tempfile.TemporaryDirectory() as directory:
            original_path = Path(directory, "original.exe")
            original_path.write_bytes(source)
            image = patcher.PEImage(original_path)
            injection = patcher.plan_new_executable_section(image, 0x61)

        plan = {
            "target": {"sha256": patcher.hashlib.sha256(source).hexdigest().upper()},
            "call_patch": {
                "file_offset": 0x410,
                "expected_bytes": bytes(5),
                "replacement_bytes": b"\xE8\x01\x02\x03\x04",
            },
            "helper": {**injection, "payload": b"\x90\xC3"},
        }
        patched = patcher.build_patched_image(source, plan)
        with tempfile.TemporaryDirectory() as directory:
            patched_path = Path(directory, "patched.exe")
            patched_path.write_bytes(patched)
            parsed = patcher.PEImage(patched_path)

        patcher.validate_added_section(parsed, plan["helper"])
        self.assertEqual(parsed.sections[-1].name, ".bca")
        self.assertTrue(parsed.sections[-1].executable)
        self.assertEqual(patched[injection["file_offset"] : injection["file_offset"] + 2], b"\x90\xC3")
        self.assertEqual(len(patched), injection["file_offset"] + injection["raw_size"])

    def test_new_section_apply_and_restore(self):
        source = bytes(self.make_minimal_pe())
        payload = b"\x90\xC3"
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "game.exe")
            target.write_bytes(source)
            injection = patcher.plan_new_executable_section(
                patcher.PEImage(target), 0x61
            )
            plan = {
                "target": {
                    "sha256": patcher.hashlib.sha256(source).hexdigest().upper()
                },
                "call_patch": {
                    "va": 0x140001010,
                    "rva": 0x1010,
                    "file_offset": 0x410,
                    "expected_bytes": bytes(5),
                    "replacement_bytes": b"\xE8\x01\x02\x03\x04",
                    "original_target": 0x140001100,
                    "replacement_target": injection["va"],
                },
                "helper": {
                    **injection,
                    "payload": payload,
                    "payload_sha256": patcher.hashlib.sha256(payload).hexdigest().upper(),
                },
            }
            receipt = patcher.apply_plan(target, plan)
            patched = target.read_bytes()
            patcher.validate_added_section(patcher.PEImage(target), plan["helper"])
            self.assertEqual(receipt["status"], "applied")
            self.assertEqual(patched, patcher.build_patched_image(source, plan))

            restore = patcher.restore_backup(target, Path(receipt["backup"]), plan)
            self.assertEqual(restore["status"], "restored")
            self.assertEqual(target.read_bytes(), source)

    def test_scheduler_structure_recovers_sib_encoded_colony_register(self):
        image = self.make_minimal_pe()
        image[0x400 : 0x400 + 30] = bytes.fromhex(
            "49 8B 4C 24 08"  # mov rcx, [r12 + 8]
            "E8 00 00 00 00"  # call
            "84 C0"           # test al, al
            "0F 85 0E 00 00 00"  # jne 0x140001020
            "41 83 7C 24 24 00"  # cmp dword ptr [r12 + 0x24], 0
            "0F 84 02 00 00 00"  # je 0x140001020
        )
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory, "scheduler.exe")
            executable.write_bytes(image)
            scheduler = patcher.locate_scheduler(patcher.PEImage(executable))

        self.assertEqual(scheduler["colony_register"], "r12")
        self.assertEqual(scheduler["signature_va"], 0x140001000)
        self.assertEqual(scheduler["scheduler_exit_va"], 0x140001020)


if __name__ == "__main__":
    unittest.main()
