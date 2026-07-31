"""Verify that a timed-out pybag session detaches without killing its target."""

from __future__ import annotations

import argparse

from pybag import DbgEng, UserDbg


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("--timeout", type=int, default=2)
    args = parser.parse_args()

    debugger = UserDbg()
    attached = False
    detached = False
    try:
        debugger.attach(args.pid, initial_break=True)
        attached = True
        for _ in range(16):
            if not debugger.go(timeout=args.timeout):
                break
        else:
            raise RuntimeError("Target kept producing debug events; timeout was not tested")

        if not debugger._ev.wait(5):
            raise RuntimeError("DbgEng did not acknowledge the timeout interrupt")

        debugger._client.EndSession(DbgEng.DEBUG_END_ACTIVE_DETACH)
        detached = True
        print("detached_after_timeout")
    finally:
        if attached and not detached:
            try:
                debugger._client.EndSession(DbgEng.DEBUG_END_ACTIVE_DETACH)
            except Exception as error:
                print(f"detach_failed: {error!r}")
        debugger.Release()


if __name__ == "__main__":
    main()
