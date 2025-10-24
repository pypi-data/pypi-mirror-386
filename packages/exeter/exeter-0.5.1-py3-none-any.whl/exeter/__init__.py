#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""This package makes it easy to make a number of test cases which can be
invoked by an external runner"""

from .asserts import assert_eq, assert_raises
from .manifest import main, register, register_pipe, test, current_testid, \
    current_test_index, TestCase
from .protocol import skip
from .scenario import Scenario, scenariotest

__all__ = ['assert_raises', 'assert_eq', 'current_testid',
           'current_test_index', 'main', 'register', 'register_pipe', 'skip',
           'test', 'TestCase', 'Scenario', 'scenariotest']
