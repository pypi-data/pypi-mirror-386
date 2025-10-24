#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Exeter test protocol helpers"""

import sys


__all__ = ['skip', 'EXIT_PASS', 'EXIT_SKIP', 'EXIT_HARD_FAILURE']


# Exit codes for exeter protocol
EXIT_PASS = 0
EXIT_SKIP = 77
EXIT_HARD_FAILURE = 99


def skip(reason: str) -> None:
    """Skip the current test"""
    print(f"SKIP: {reason}")
    sys.exit(EXIT_SKIP)
