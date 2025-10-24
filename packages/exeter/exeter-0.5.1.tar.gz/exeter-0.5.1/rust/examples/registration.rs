// SPDX-License-Identifier: MIT
//
// Copyright Red Hat
// Author: David Gibson <david@gibson.dropbear.id.au>

//! Test registration functionality and polymorphic FnOnce support

fn register_returns_testcase() {
    let mut m = exeter::Manifest::new();
    let c: &mut exeter::manifest::TestCase = m.register("register.test", || {});
    c.set_description("This is a test description");
}

fn simple_function() {
    // Simple function pointer test
}

fn main() {
    let mut m = exeter::Manifest::new();

    m.register("register_returns_testcase", register_returns_testcase)
        .set_description("Test that register returns a TestCase");

    m.register("function_pointer", simple_function)
        .set_description("Test that function pointers can be registered");

    let c = m.register("simple_closure", || {
        // Simple closure without captures
    });
    c.set_description("Test that simple closures can be registered");

    let captured_value = "test_value".to_string();
    let c = m.register("capturing_closure", move || {
        // This closure captures `captured_value` by move
        assert_eq!(captured_value, "test_value");
    });
    c.set_description("Test that closures capturing variables can be registered");

    m.main();
}
