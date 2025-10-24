#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Self test assertion helpers"""

from typing import Optional

import exeter


# assert_raises

class TestError(Exception):
    """Sample exception class for tests"""


def raise_arg(exc: Optional[type[BaseException]] = None) -> None:
    """Raise an exception of the given class, or do nothing if None is
    passed"""
    if exc is not None:
        raise exc()


@exeter.test
def assert_raises() -> None:
    """exeter.assert_raises passes if correct exception raised"""
    exeter.assert_raises(TestError, raise_arg, TestError)


@exeter.test
def assert_raises_no_exc() -> None:
    """exeter.assert_raises fails if no exception raised"""
    try:
        exeter.assert_raises(TestError, raise_arg, None)
    except AssertionError:
        return
    assert False


@exeter.test
def assert_raises_wrong_exc() -> None:
    """exeter.assert_raises fails if incorrect exception is raised"""
    try:
        exeter.assert_raises(TestError, raise_arg, TypeError)
    except TypeError:
        return
    assert False


# assert_eq

@exeter.test
def assert_eq() -> None:
    """exeter.assert_eq passes if given values are equal"""
    for x in [17, "hello"]:
        exeter.assert_eq(x, x)


@exeter.test
def assert_eq_neq() -> None:
    """exeter.assert_eq fails if given values are not equal"""
    exeter.assert_raises(AssertionError, exeter.assert_eq, 1, 2)


if __name__ == '__main__':
    exeter.main()
