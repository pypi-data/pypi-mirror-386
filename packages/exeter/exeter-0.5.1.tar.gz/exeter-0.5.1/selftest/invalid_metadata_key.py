#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>
#
# Test program that outputs invalid metadata key for testing exetool validation

import sys

if len(sys.argv) > 1 and sys.argv[1] == "--exeter":
    print("exeter test protocol 0.4.1")
    sys.exit(0)
elif len(sys.argv) > 1 and sys.argv[1] == "--list":
    print("test1")
    sys.exit(0)
elif len(sys.argv) > 2 and sys.argv[1] == "--metadata":
    if sys.argv[2] == "test1":
        print("invalid-key=value")  # Invalid: key contains dash
        sys.exit(0)
    else:
        print(f"No such testcase '{sys.argv[2]}'", file=sys.stderr)
        sys.exit(99)
else:
    print(f"Running test {sys.argv[1] if len(sys.argv) > 1 else 'unknown'}")
