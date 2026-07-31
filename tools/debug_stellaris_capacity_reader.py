"""Capture the first queue-capacity reader outside the known progress updater."""

from __future__ import annotations

import argparse
from pathlib import Path

from pybag import DbgEng, UserDbg

from debug_stellaris_session import detach_session, go_or_timeout


IGNORED_RANGES = (
    (0x8032B0, 0x803510),    # Construction progress updater.
    (0x1673500, 0x1673900),  # Planet build-queue item UI state.
    (0x15C9200, 0x15C9500),  # Aggregate build-queue UI refresh.
)


def module_base(debugger: UserDbg, module_name: str) -> int:
    wanted = module_name.lower()
    for names, parameters in debugger.mod.modules():
        values = [
            value.decode(errors="replace").lower()
            if isinstance(value, bytes)
            else value.lower()
            for value in names[:2]
        ]
        if wanted in values:
            return parameters.Base
    raise RuntimeError(f"Module not found: {module_name}")


def append_command(output, debugger: UserDbg, command: str) -> None:
    output.write(f"=== {command} ===\n")
    try:
        output.write(debugger.cmd(command))
    except Exception as error:
        output.write(f"command failed: {error!r}\n")
    output.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("address", type=lambda value: int(value, 0))
    parser.add_argument("report", type=Path)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    args.report.parent.mkdir(parents=True, exist_ok=True)
    debugger = UserDbg()
    breakpoint = None
    attached = False
    ignored_hits = 0
    captured_pc = 0

    def on_read(_breakpoint, active_debugger: UserDbg) -> int:
        nonlocal ignored_hits, captured_pc
        pc = active_debugger.reg.get_pc()
        offset = pc - base
        for start, end in IGNORED_RANGES:
            if start <= offset < end:
                ignored_hits += 1
                return DbgEng.DEBUG_STATUS_GO
        captured_pc = pc
        return DbgEng.DEBUG_STATUS_BREAK

    try:
        debugger.attach(args.pid, initial_break=True)
        attached = True
        base = module_base(debugger, "stellaris")
        breakpoint = debugger.ba(
            args.address,
            handler=on_read,
            size=4,
            access=DbgEng.DEBUG_BREAK_READ,
            threadid=0,
        )
        go_or_timeout(debugger, args.timeout)

        with args.report.open("w", encoding="ascii", errors="replace") as output:
            output.write("status: external capacity reader captured\n")
            output.write(f"pid: {debugger.pid}\n")
            output.write(f"stellaris_base: 0x{base:016X}\n")
            output.write(f"capacity_address: 0x{args.address:016X}\n")
            output.write(f"capacity_value: {int.from_bytes(debugger.read(args.address, 4), 'little')}\n")
            output.write(f"ignored_updater_hits: {ignored_hits}\n")
            output.write(f"pc: 0x{captured_pc:016X}\n")
            output.write(f"static_offset: 0x{captured_pc - base:X}\n\n")
            for name in ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9"):
                output.write(f"{name}: 0x{debugger.reg[name]:016X}\n")
            output.write("\n")
            append_command(output, debugger, "k")
            append_command(output, debugger, "u @rip-30 L60")
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
