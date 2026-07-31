"""Capture one execution of the colony-automation shared eligibility gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from pybag import DbgEng, UserDbg

from debug_stellaris_session import detach_session, go_or_timeout


ELIGIBILITY_GATE_OFFSET = 0xEEAFB0


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
    parser.add_argument("report", type=Path)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    args.report.parent.mkdir(parents=True, exist_ok=True)
    debugger = UserDbg()
    entry_breakpoint = None
    return_breakpoint = None
    attached = False

    try:
        debugger.attach(args.pid, initial_break=True)
        attached = True
        entry_breakpoint = debugger.breakpoints.set(
            f"stellaris+0x{ELIGIBILITY_GATE_OFFSET:x}", oneshot=True
        )
        go_or_timeout(debugger, args.timeout)

        stack_pointer = debugger.reg.get_sp()
        return_address = int.from_bytes(debugger.read(stack_pointer, 8), "little")
        with args.report.open("w", encoding="ascii", errors="replace") as output:
            output.write("status: eligibility gate entry captured\n")
            output.write(f"pid: {debugger.pid}\n")
            output.write(f"return_address: 0x{return_address:016X}\n\n")
            for command in (
                "lm m stellaris",
                "r rip rsp rcx rdx r8 r9 r10 r11 rax",
                "k",
                "u @rip-20 L32",
            ):
                append_command(output, debugger, command)

            entry_breakpoint = None
            return_breakpoint = debugger.breakpoints.set(return_address, oneshot=True)
            go_or_timeout(debugger, args.timeout)

            output.write("status: eligibility gate return captured\n\n")
            for command in (
                "r rip rsp rax al rcx rdx r8 r9 r10 r11",
                "k",
                "u @rip-20 L32",
            ):
                append_command(output, debugger, command)
    except Exception as error:
        if args.report.exists():
            with args.report.open("a", encoding="ascii", errors="replace") as output:
                output.write(f"status: error: {error!r}\n")
        else:
            args.report.write_text(f"status: error: {error!r}\n", encoding="ascii")
        raise
    finally:
        if attached:
            for breakpoint_id in (entry_breakpoint, return_breakpoint):
                if breakpoint_id is not None:
                    try:
                        debugger.breakpoints.remove(breakpoint_id)
                    except Exception:
                        pass
            detach_session(debugger)
        debugger.Release()


if __name__ == "__main__":
    main()
