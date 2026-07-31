"""Capture the colony-automation scheduler eligibility virtual call via DbgEng."""

from __future__ import annotations

import argparse
from pathlib import Path

from pybag import DbgEng, UserDbg

from debug_stellaris_session import detach_session, go_or_timeout


SCHEDULER_VIRTUAL_CALL_OFFSET = 0x73B5B7


def write_report(report: Path, debugger: UserDbg, status: str) -> None:
    with report.open("w", encoding="ascii", errors="replace") as output:
        output.write(f"status: {status}\n")
        output.write(f"pid: {debugger.pid}\n\n")
        for command in ("lm m stellaris", "r", "k", "u @rip-20 L24"):
            output.write(f"=== {command} ===\n")
            try:
                output.write(debugger.cmd(command))
            except Exception as error:  # Keep the partial capture useful.
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
    breakpoint_id = None
    attached = False
    try:
        debugger.attach(args.pid, initial_break=True)
        attached = True
        breakpoint_id = debugger.breakpoints.set(
            f"stellaris+0x{SCHEDULER_VIRTUAL_CALL_OFFSET:x}", oneshot=True
        )
        go_or_timeout(debugger, args.timeout)
        write_report(args.report, debugger, debugger.exec_status())
    except Exception as error:
        if attached:
            write_report(args.report, debugger, f"error: {error!r}")
        else:
            args.report.write_text(f"attach error: {error!r}\n", encoding="ascii", errors="replace")
        raise
    finally:
        if attached:
            try:
                if breakpoint_id is not None:
                    debugger.breakpoints.remove(breakpoint_id)
            except Exception:
                pass
            detach_session(debugger)
        debugger.Release()


if __name__ == "__main__":
    main()
