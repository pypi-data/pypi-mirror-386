#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Test script to verify version consistency across the project"""

import re
import subprocess
import sys


def get_exetool_version() -> str:
    """Extract version from exetool script"""
    exetool_path = sys.argv[2]

    # Run exetool --version and parse output
    result = subprocess.run(
        [exetool_path, '--version'],
        capture_output=True,
        text=True,
        check=True
    )

    # Expected format: "exetool 0.4.1"
    match = re.search(r'exetool\s+(\S+)', result.stdout)
    if not match:
        raise ValueError(
            f"Could not parse exetool version from: {result.stdout}")

    return match.group(1)


def main() -> int:
    """Test that meson and exetool versions match"""
    if len(sys.argv) != 3:
        print("Usage: "
              "test_version_consistency.py <meson_version> <exetool_path>")
        return 1

    meson_version = sys.argv[1]
    exetool_version = get_exetool_version()

    print(f"Meson project version: {meson_version}")
    print(f"Exetool version: {exetool_version}")

    if meson_version == exetool_version:
        print("✓ Versions match")
        return 0
    else:
        print("✗ Version mismatch!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
