#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Managing the manifest of registered exeter tests"""

import functools
import inspect
import re
import signal
import sys
import traceback
from types import ModuleType
from typing import Any, Callable, Optional, ParamSpec


__all__ = ['main', 'register', 'register_pipe', 'test', 'TestCase',
           'id_from_fn']


class HardError(Exception):
    """Exception which should cause a hard error (exit code 99) for
    the test runner"""


class BadTestId(HardError):
    """Exception when we try to register an exeter test with an
    invalid test id"""


class DuplicateTestId(HardError):
    """Exception when we try to register two exeter tests with the
    same test id"""


class NotRunningTest(HardError):
    """Exception when we try to get info about the current test,
    but we're not running a test"""


TESTID_RE = re.compile('[a-zA-Z0-9.;_]+')
Ps = ParamSpec("Ps")


def id_from_fn(f: Callable[..., Any]) -> str:
    """Generate exeter test ID from callable's qualname, fixing .<locals>.
    to .."""
    return f.__qualname__.replace('.<locals>.', '..')


class TestCase:
    """A single exeter test case"""

    description: str

    def __init__(self, testid: str, func: Callable[..., None],
                 *args: Any, **kwargs: Any) -> None:
        self.testid = testid
        self.func = functools.partial(func, *args, **kwargs)

        if hasattr(func, '__doc__') and func.__doc__:
            description = func.__doc__.splitlines()[0].strip()
            try:
                # Bind arguments to parameters using function signature
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                description = description.format(*bound_args.args,
                                                 **bound_args.arguments)
            except (KeyError, IndexError, ValueError, TypeError):
                pass
            self.set_description(description)

    def run(self) -> None:
        """Run the test"""
        return self.func()

    def __str__(self) -> str:
        return f"TestCase(testid='{self.testid}'"

    def metadata(self) -> dict[str, str]:
        """Return testcase metadata"""
        d = {}
        if hasattr(self, 'description'):
            d['description'] = self.description
        return d

    def set_description(self, description: str) -> None:
        """Set the description for this test case"""
        self.description = description


manifest: dict[str, TestCase] = {}


def register(testid: str, f: Callable[Ps, None],
             *args: Ps.args, **kwargs: Ps.kwargs) -> TestCase:
    """Register callable f with arguments *args and **kwargs as an
    exeter testcase under the id testid"""
    if not TESTID_RE.match(testid):
        raise BadTestId(testid)
    if testid in manifest:
        raise DuplicateTestId(testid)
    c = TestCase(testid, f, *args, **kwargs)
    manifest[testid] = c
    return c


def register_pipe(testid: str, *fs: Callable[..., Any]) -> TestCase:
    """Register a pipeline (composition) of functions as an exeter
    testcase.  When the testcase is executed the first function given
    is called with no arguments, its return value is passed to the
    second and so forth."""
    def pipefn() -> None:
        args: tuple[Any, ...] = ()
        for f in fs:
            args = f(*args)
            if not isinstance(args, tuple):
                args = (args,)
    return register(testid, pipefn)


def test(f: Callable[[], None]) -> Callable[[], None]:
    """Decorator to automatically register function as an exeter test
    under its qualified function name"""
    testid = id_from_fn(f)
    if f.__module__ != '__main__':
        testid = f"{f.__module__}.{testid}"
    register(testid, f)
    return f


def __usage(scriptname: Optional[str], error: bool = False) -> None:
    print(
        f"""Usage: {scriptname} [OPTIONS] <testcase id>

Exeter (Python 3) based tests.

Options:
    --exeter         display protocol version and exit
    --help           display this help and exit
    --list           list test cases and exit
    --metadata <id>  output metadata for test case and exit
""")
    if error:
        sys.exit(1)
    else:
        sys.exit()


def __list_tests(args: list[str]) -> None:
    if not args:
        for testid in manifest:
            print(f"{testid}")
    else:
        for testid in args:
            if testid not in manifest:
                print(f"No such testcase '{testid}'", file=sys.stderr)
                sys.exit(99)
            print(f"{testid}")
    sys.exit(0)


def __escape_value(value: str) -> str:
    """Escape value using minimal C-style escape sequences"""
    return (value.replace('\\', '\\\\')
                 .replace('\n', '\\n')
                 .replace('\0', '\\0'))


def __metadata(testid: str) -> None:
    """Output metadata for the specified test"""
    if testid not in manifest:
        print(f"No such testcase '{testid}'", file=sys.stderr)
        sys.exit(99)

    testcase = manifest[testid]
    for key, value in testcase.metadata().items():
        print(f"{key}={__escape_value(value)}")
    sys.exit(0)


_current_testid: str | None = None


def current_testid() -> str:
    if _current_testid is None:
        raise NotRunningTest
    return _current_testid


def current_test_index() -> int:
    for i, n in enumerate(manifest.keys()):
        if n == current_testid():
            return i
    assert False


def main(args: Optional[list[str]] = None) -> None:
    """Main program to implement an exeter test program"""
    global _current_testid

    def signal_handler(signum: int, frame: Any) -> None:
        """Convert signals to SystemExit to trigger context manager cleanup"""
        raise SystemExit(128 + signum)

    # Handle termination signals that support cleanup
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)

    try:
        mainmod: ModuleType = sys.modules['__main__']
        mainfile: Optional[str] = mainmod.__file__  # pylint: disable=E1101
        if args is None:
            args = sys.argv[1:]

        if not args or args == ['--help']:
            __usage(mainfile)

        if args[0] == '--exeter':
            print("exeter test protocol 0.4.1")
            sys.exit(0)

        if args[0] == '--list':
            __list_tests(args[1:])

        if args[0] == '--metadata':
            if len(args) != 2:
                __usage(mainfile, error=True)
            __metadata(args[1])

        if len(args) > 1:
            __usage(mainfile, error=True)

        _current_testid = args[0]
        testcase = manifest[_current_testid]
        assert isinstance(testcase, TestCase)
    except Exception:  # pylint: disable=W0718
        print(traceback.format_exc())
        sys.exit(99)

    print(f"exeter (py3): Running test {_current_testid}")
    testcase.run()
