#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Trivial exeter tests in Python"""

import exeter


@exeter.test
def trivial_pass() -> None:
    """Trivially pass"""


@exeter.test
def trivial_fail() -> None:
    """Trivially fail"""
    assert False


@exeter.test
def trivial_skip() -> None:
    """Trivially skip"""
    exeter.skip("This test is trivially skipped")


if __name__ == '__main__':
    exeter.main()
