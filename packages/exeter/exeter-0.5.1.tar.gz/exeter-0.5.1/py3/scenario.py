#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Assorted Python languange tests for Scenarios"""

import contextlib
import dataclasses
from typing import Iterator

import exeter


@dataclasses.dataclass
class SimpleScenario(exeter.Scenario):
    val: bool

    @exeter.scenariotest
    def pass_if(self) -> None:
        assert self.val

    @exeter.scenariotest
    def fail_if(self) -> None:
        assert not self.val


@SimpleScenario.test
@contextlib.contextmanager
def setup_true() -> Iterator[SimpleScenario]:
    yield SimpleScenario(True)


@SimpleScenario.test
@contextlib.contextmanager
def setup_false() -> Iterator[SimpleScenario]:
    yield SimpleScenario(False)


@dataclasses.dataclass
class CompoundScenario(exeter.Scenario):
    val1: bool
    val2: bool

    @exeter.scenariotest
    def is_equal(self) -> None:
        assert self.val1 == self.val2

    @SimpleScenario.subscenario
    def test_val1(self) -> SimpleScenario:
        return SimpleScenario(self.val1)

    @SimpleScenario.subscenario
    def test_val2(self) -> SimpleScenario:
        return SimpleScenario(self.val2)


@CompoundScenario.test
@contextlib.contextmanager
def setup_ff() -> Iterator[CompoundScenario]:
    yield CompoundScenario(False, False)


@CompoundScenario.test
@contextlib.contextmanager
def setup_ft() -> Iterator[CompoundScenario]:
    yield CompoundScenario(False, True)


@CompoundScenario.test
@contextlib.contextmanager
def setup_tf() -> Iterator[CompoundScenario]:
    yield CompoundScenario(True, False)


@CompoundScenario.test
@contextlib.contextmanager
def setup_tt() -> Iterator[CompoundScenario]:
    yield CompoundScenario(True, True)


def outer_scenario_function() -> None:
    """Function to test Scenario.test decorator on local functions"""
    @SimpleScenario.test
    @contextlib.contextmanager
    def local_scenario_setup() -> Iterator[SimpleScenario]:
        """Test that Scenario.test works on local functions"""
        yield SimpleScenario(True)


def outer_class_function() -> None:
    """Function to test local Scenario classes"""

    class LocalScenario(exeter.Scenario):
        @exeter.scenariotest
        def local_test(self) -> None:
            pass

    @LocalScenario.test
    @contextlib.contextmanager
    def local_class_setup() -> Iterator[LocalScenario]:
        """Test that local Scenario classes work"""
        yield LocalScenario()


# Register the local scenario test by calling the outer function
outer_scenario_function()

# Register the local class test by calling the outer function
outer_class_function()


# Test explicit Scenario.register calls
@dataclasses.dataclass
class ParameterizedScenario(exeter.Scenario):
    name: str
    value: int

    @exeter.scenariotest
    def check_positive(self) -> None:
        assert self.value > 0

    @exeter.scenariotest
    def check_name_length(self) -> None:
        assert len(self.name) > 0


@contextlib.contextmanager
def create_parameterized(name: str, value: int) \
        -> Iterator[ParameterizedScenario]:
    yield ParameterizedScenario(name, value)


# Test register with parameters
ParameterizedScenario.register("explicit_positive", create_parameterized,
                               "test", 42)
ParameterizedScenario.register("explicit_negative", create_parameterized,
                               "neg", -5)
ParameterizedScenario.register("explicit_zero", create_parameterized,
                               "zero", 0)


@contextlib.contextmanager
def create_simple_with_msg(msg: str) -> Iterator[SimpleScenario]:
    yield SimpleScenario(msg == "true")


# Test register with single parameter
SimpleScenario.register("explicit_true_msg", create_simple_with_msg, "true")
SimpleScenario.register("explicit_false_msg", create_simple_with_msg, "false")


if __name__ == '__main__':
    exeter.main()
