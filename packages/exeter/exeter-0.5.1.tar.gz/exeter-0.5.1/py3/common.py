#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>
#
# Common code for passing and failing examples

"""Helpful functions across multiple Python exeter examples"""

from typing import Any


def pass_if(val: Any) -> None:
    """Fail a test if the given parameter is not true"""
    print(f"pass_if({val})")
    assert val
