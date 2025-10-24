// SPDX-License-Identifier: MIT
//
// Copyright Red Hat
// Author: David Gibson <david@gibson.dropbear.id.au>

//! Tests for current_testid()

use exeter::current_testid;

fn test1() {
    // Test that current_testid() gives running test id
    assert_eq!(current_testid().unwrap(), "test1");
}

fn main() {
    let mut m = exeter::Manifest::new();

    m.register("test1", test1)
        .set_description("exeter::current_testid() gives running test id");

    // Register with alias name
    m.register("test2", test1)
        .set_description("exeter::current_testid() gives aliased test id");

    m.main();
}
