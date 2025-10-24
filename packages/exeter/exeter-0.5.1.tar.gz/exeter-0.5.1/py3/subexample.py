#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Sub-module for checking that exeter properly handles tests from
imported modules"""

import exeter


@exeter.test
def trivial() -> None:
    """Trivial test in submodule"""
