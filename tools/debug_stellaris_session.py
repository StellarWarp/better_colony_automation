"""Shared lifecycle handling for the Stellaris DbgEng capture scripts."""

from __future__ import annotations

from pybag import DbgEng, UserDbg


def go_or_timeout(debugger: UserDbg, timeout: int) -> None:
    if debugger.go(timeout=timeout):
        return

    if not debugger._ev.wait(5):
        raise RuntimeError("DbgEng did not acknowledge the timeout interrupt")
    raise TimeoutError(f"No matching debug event within {timeout} seconds")


def detach_session(debugger: UserDbg) -> None:
    debugger._client.EndSession(DbgEng.DEBUG_END_ACTIVE_DETACH)
