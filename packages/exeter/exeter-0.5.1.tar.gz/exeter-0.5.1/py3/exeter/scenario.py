#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Helpers for constructing scenarios in which a number of tests can run"""

from __future__ import annotations

import contextlib
from typing import Callable, Iterable, Iterator, ParamSpec, Self, TypeVar

from .manifest import register, id_from_fn


_SCENARIO_TEST_FLAG = "__scenario_test__"
_SUBSCENARIO_FLAG = "__subscenario__"


ACM = contextlib.AbstractContextManager
Ps = ParamSpec("Ps")


class Scenario:
    """Base class for a scenario in which a number of tests can run"""

    @classmethod
    def scenario_tests(cls) -> Iterable[Callable[[Self], None]]:
        for n in dir(cls):
            f = getattr(cls, n)
            if hasattr(f, _SCENARIO_TEST_FLAG):
                yield f

    @classmethod
    def subscenarios(cls) \
            -> Iterable[tuple[type[Scenario], Callable[[Self], Scenario]]]:
        for n in dir(cls):
            f = getattr(cls, n)
            if not hasattr(f, _SUBSCENARIO_FLAG):
                continue
            subscncls = getattr(f, _SUBSCENARIO_FLAG)
            yield (subscncls, f)

    @classmethod
    def register(cls: type[Self], basename: str,
                 ctxfn: Callable[Ps, ACM[Self]],
                 *args: Ps.args, **kwargs: Ps.kwargs) -> None:
        def wrap(test: Callable[[Self], None]) -> None:
            with ctxfn(*args, **kwargs) as scn:
                test(scn)

        for t in cls.scenario_tests():
            name = f"{basename};;{id_from_fn(t)}"
            register(name, wrap, t)

        @contextlib.contextmanager
        def wrap_setup(subf: Callable[[Self], Scenario]) -> Iterator[Scenario]:
            with ctxfn(*args, **kwargs) as superscn:
                yield subf(superscn)

        for (subscncls, subf) in cls.subscenarios():
            name = f"{basename};;{id_from_fn(subf)}"
            subscncls.register(name, wrap_setup, subf)

    @classmethod
    def test(cls: type[Self], setup: Callable[[], ACM[Self]]) \
            -> Callable[[], ACM[Self]]:
        cls.register(f"{id_from_fn(setup)}", setup)
        return setup

    SuperS = TypeVar("SuperS", bound="Scenario")

    @classmethod
    def subscenario(cls, subscn: Callable[[SuperS], Self]) \
            -> Callable[[SuperS], Self]:
        setattr(subscn, _SUBSCENARIO_FLAG, cls)
        return subscn


S = TypeVar("S", bound=Scenario)


def scenariotest(f: Callable[[S], None]) -> Callable[[S], None]:
    setattr(f, _SCENARIO_TEST_FLAG, True)
    return f
