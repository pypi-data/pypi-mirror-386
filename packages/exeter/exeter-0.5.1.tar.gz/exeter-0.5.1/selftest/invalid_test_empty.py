#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>
#
# Test program that outputs empty line for testing exetool validation

import sys

if len(sys.argv) > 1 and sys.argv[1] == "--exeter":
    print("exeter test protocol 0.2.0")
    sys.exit(0)
elif len(sys.argv) > 1 and sys.argv[1] == "--list":
    print("valid_test")
    print("")  # Invalid: empty line
    sys.exit(0)
else:
    print(f"Running test {sys.argv[1] if len(sys.argv) > 1 else 'unknown'}")
