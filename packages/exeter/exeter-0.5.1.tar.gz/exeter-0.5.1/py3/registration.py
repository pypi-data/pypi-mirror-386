#!/usr/bin/env python3

import exeter


@exeter.test
def register_returns_testcase() -> None:
    """Test that register returns a TestCase instance"""

    testcase = exeter.register("sample.id", lambda: None)

    assert isinstance(testcase, exeter.TestCase)
    assert testcase.testid == "sample.id"


@exeter.test
def register_pipe_returns_testcase() -> None:
    """Test that register_pipe returns a TestCase instance"""

    testcase = exeter.register_pipe("pipe.sample.id", lambda: 42,
                                    lambda x: x * 2)

    assert isinstance(testcase, exeter.TestCase)
    assert testcase.testid == "pipe.sample.id"


@exeter.test
def desc_single_line() -> None:
    """Test that single line docstrings are used as description"""

    def test_func() -> None:
        """This is a single line description"""
        pass

    testcase = exeter.register("single.line.test", test_func)
    assert testcase.description == "This is a single line description"


@exeter.test
def desc_first_line_only() -> None:
    """Test that only the first line of multiline docstrings is used"""

    def test_func() -> None:
        """This is the first line
        This is the second line
        This is the third line
        """
        pass

    testcase = exeter.register("first.line.test", test_func)
    assert testcase.description == "This is the first line"


@exeter.test
def desc_strips_whitespace() -> None:
    """Test that whitespace is stripped from the first line"""

    def test_func() -> None:
        """   This has leading and trailing spaces   """
        pass

    testcase = exeter.register("whitespace.test", test_func)
    assert testcase.description == "This has leading and trailing spaces"


@exeter.test
def desc_format_positional() -> None:
    """Test that positional format specifiers work in descriptions"""

    def test_func(value: int) -> None:
        """Test with value {}"""
        pass

    testcase = exeter.register("format.positional.test", test_func, 42)
    assert testcase.description == "Test with value 42"


@exeter.test
def desc_format_keyword() -> None:
    """Test that keyword format specifiers work in descriptions"""

    def test_func(name: str) -> None:
        """Test with name {name}"""
        pass

    testcase = exeter.register("format.keyword.test", test_func, name="alice")
    assert testcase.description == "Test with name alice"


@exeter.test
def desc_format_pos_arg_named_spec() -> None:
    """Test positional arguments with named format specifiers"""

    def test_func(name: str) -> None:
        """Test with name {name}"""
        pass

    testcase = exeter.register("format.pos.arg.named.spec.test", test_func,
                               "bob")
    assert testcase.description == "Test with name bob"


@exeter.test
def desc_format_kwarg_pos_spec() -> None:
    """Test keyword arguments with positional format specifiers"""

    def test_func(name: str) -> None:
        """Test with name {}"""
        pass

    testcase = exeter.register("format.kwarg.pos.spec.test", test_func,
                               name="alice")
    assert testcase.description == "Test with name alice"


@exeter.test
def desc_format_mixed() -> None:
    """Test that mixed format specifiers work in descriptions"""

    def test_func(a: int, name: str) -> None:
        """Test {} with name {name}"""
        pass

    testcase = exeter.register("format.mixed.test", test_func, 123, name="bob")
    assert testcase.description == "Test 123 with name bob"


@exeter.test
def desc_format_invalid() -> None:
    """Test that invalid format specifiers fall back to original"""

    def test_func(value: int) -> None:
        """Test with missing {missing_key}"""
        pass

    testcase = exeter.register("format.invalid.test", test_func, 42)
    assert testcase.description == "Test with missing {missing_key}"


if __name__ == "__main__":
    exeter.main()
