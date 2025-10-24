#! /usr/bin/env python3
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>
#
# selftest/checklist.py - Order-independent comparison of file
#                         contents against expected lists

import sys
from itertools import combinations


def checklist(actual: str, *lists: str) -> None:
    """Compare file contents in an order-independent way.

    Checks that the actual file contains exactly the union of all expected
    list files, ignoring line order. Expected files must not overlap.
    """
    lactual = frozenset(open(actual).readlines())
    # Load all list files
    expected = [frozenset(open(name).readlines()) for name in lists]

    # Check for overlaps between any pair of lists
    for (i, a), (j, b) in combinations(enumerate(expected), 2):
        inter = a.intersection(b)
        if inter:
            print(f"{inter} in both {lists[i]} and {lists[j]}",
                  file=sys.stderr)
            sys.exit(99)

    # Check if union of all lists equals actual
    lx = frozenset().union(*expected)

    if lactual == lx:
        sys.exit(0)

    # Report differences
    da = [x.strip() for x in lactual - lx]
    if da:
        names = ', '.join(lists)
        print(f"In {actual} but not in any of {names}: {da}")

    # Report items in expected lists but not in actual
    for i, exp in enumerate(expected):
        diff = [x.strip() for x in exp - lactual]
        if diff:
            print(f"In {lists[i]} but not in {actual}: {diff}")

    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: checklist.py <actual_file> <expected_file...>",
              file=sys.stderr)
        sys.exit(2)
    checklist(sys.argv[1], *sys.argv[2:])
