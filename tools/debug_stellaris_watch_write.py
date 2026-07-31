"""Capture the first write to a selected Stellaris runtime address."""

from __future__ import annotations

import argparse
from pathlib import Path

from pybag import DbgEng, UserDbg

from debug_stellaris_session import detach_session, go_or_timeout


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
    parser.add_argument("--size", type=int, choices=(1, 2, 4, 8), default=8)
    parser.add_argument("--all-threads", action="store_true")
    args = parser.parse_args()

    args.report.parent.mkdir(parents=True, exist_ok=True)
    debugger = UserDbg()
    breakpoint = None
    attached = False
    try:
        debugger.attach(args.pid, initial_break=True)
        attached = True
        breakpoint = debugger.ba(
            args.address,
            oneshot=True,
            size=args.size,
            access=DbgEng.DEBUG_BREAK_WRITE,
            threadid=0 if args.all_threads else None,
        )
        go_or_timeout(debugger, args.timeout)
        breakpoint = None

        with args.report.open("w", encoding="ascii", errors="replace") as output:
            output.write("status: write captured\n")
            output.write(f"pid: {debugger.pid}\n")
            output.write(f"watched_address: 0x{args.address:016X}\n")
            output.write(f"pc: 0x{debugger.reg.get_pc():016X}\n")
            for name in ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11"):
                try:
                    output.write(f"{name}: 0x{debugger.reg[name]:016X}\n")
                except Exception as error:
                    output.write(f"{name}: <failed: {error!r}>\n")
            output.write(
                f"watched_value: {int.from_bytes(debugger.read(args.address, args.size), 'little')}\n\n"
            )
            append_command(output, debugger, "k")
            append_command(output, debugger, "u @rip-40 L80")
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
