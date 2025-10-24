#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Test SIGTERM handling with context managers"""

import contextlib
import os
import signal
import sys
from typing import Iterator

import exeter


@contextlib.contextmanager
def sysexit_success() -> Iterator[None]:
    """Succeed if the thing in context dies with SystemExit"""
    print("sysexit_success starts", file=sys.stderr)
    exc = None
    try:
        yield None
    except SystemExit as e:
        print(f"sysexit_success SystemExit {e}", file=sys.stderr)
        exc = e

    assert exc is not None
    assert exc.code


def sigself(ctx: contextlib.AbstractContextManager[None], signum: int) -> None:
    """Send a signal to ourself, in a given context"""
    with ctx:
        os.kill(os.getpid(), signum)


# Test signals both with and without cleanup handling
for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT, signal.SIGKILL):
    # Base test - signal should fail the test
    c = exeter.register(sig.name, sigself, contextlib.nullcontext(), sig)
    c.set_description(f"Test {sig.name} fails a test")

    # Test with cleanup handling
    c = exeter.register(f"catch_{sig.name}", sigself, sysexit_success(), sig)
    c.set_description(f"Test if we can clean up on {sig.name}")


if __name__ == '__main__':
    exeter.main()
