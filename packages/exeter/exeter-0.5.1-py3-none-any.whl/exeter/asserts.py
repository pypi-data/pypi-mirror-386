#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Assertion helpers"""

from typing import Any, Callable, ParamSpec


__all__ = ['assert_raises', 'assert_eq']


Ps = ParamSpec("Ps")


def assert_raises(exc: type[BaseException], fn: Callable[Ps, Any],
                  *args: Ps.args, **kwargs: Ps.kwargs) -> None:
    """Fail unless an exception of class exc is raised by the callable
    fn when invoked with the given arguments"""

    try:
        fn(*args, **kwargs)
    except exc:
        return
    assert False, f"Failed to raise {exc} exception"


def assert_eq(lhs: Any, rhs: Any) -> None:
    """Fail unless lhs and rhs are equal"""
    assert lhs == rhs, f"{lhs} == {rhs}"
