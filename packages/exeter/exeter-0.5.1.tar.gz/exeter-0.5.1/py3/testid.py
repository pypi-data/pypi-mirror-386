#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Self test retreiving testid"""

import exeter


@exeter.test
def test1() -> None:
    """exeter.current_testid() gives running test id"""
    exeter.assert_eq(exeter.current_testid(), "test1")


test2 = exeter.register('test2', test1)
test2.set_description("exeter.current_testid() gives aliased test id""")


@exeter.test
def test_index() -> None:
    """exeter.current_test_index() sanity check"""
    assert exeter.current_test_index() in range(4)


def outer_function() -> None:
    """Function to test @test decorator on local functions"""
    @exeter.test
    def local_test() -> None:
        """Test that @test works on local functions"""
        testid = exeter.current_testid()
        assert testid == "outer_function..local_test"


# Register the local test by calling the outer function
outer_function()


if __name__ == '__main__':
    exeter.main()
