#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Assorted Python languange specific exeter test cases"""

import sys

import exeter

import common

# Checking test cases in a submodule
import subexample  # noqa: F401, pylint: disable=W0611


# Basic ways to pass

@exeter.test
def exit_pass() -> None:
    """sys.exit(0)"""
    sys.exit(0)


@exeter.test
def nop_pass() -> None:
    """Do nothing"""


@exeter.test
def assert_pass() -> None:
    """assert True"""
    assert True


# Basic ways to fail

@exeter.test
def exit_fail() -> None:
    """Fail by sys.exit(1)"""
    sys.exit(1)


@exeter.test
def assert_fail() -> None:
    """Fail by assert False"""
    assert False


@exeter.test
def exception_fail() -> None:
    """Fail by raise ValueError"""
    raise ValueError


# Registering under a different name
c = exeter.register('alias_pass', exit_pass)
c.set_description('Alias for exit_pass')
c = exeter.register('alias_fail', assert_fail)
c.set_description('Alias for assert_fail')


# Functions with parameters
c = exeter.register('pass_if_true', common.pass_if, True)
c.set_description('Test registered with parameters')
c = exeter.register('pass_if_false', common.pass_if, False)
c.set_description('Failing test registered with parameters')

# Pipes
c = exeter.register_pipe('False;not;pass_if', lambda: False, lambda x: not x,
                         common.pass_if)
c.set_description('Simple composition test')

c = exeter.register_pipe('True;not;pass_if', lambda: True, lambda x: not x,
                         common.pass_if)
c.set_description('Failing simple composition test')

c = exeter.register_pipe('tuple_pipe', lambda: (1, 1), lambda x, y: x + y,
                         lambda s: s == 2, common.pass_if)
c.set_description('Pipe test with tuple handling')

if __name__ == '__main__':
    exeter.main()
