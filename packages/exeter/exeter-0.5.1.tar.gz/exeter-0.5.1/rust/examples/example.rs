// SPDX-License-Identifier: MIT
//
// Copyright Red Hat
// Author: David Gibson <david@gibson.dropbear.id.au>

//! Example exeter tests in Rust showing various ways tests can pass and fail

use std::hint::black_box;

fn nop_pass() {
    // Do nothing - should pass
}

fn exit_pass() {
    std::process::exit(0);
}

fn assert_pass() {
    assert!(black_box(true));
}

fn exit_fail() {
    std::process::exit(1);
}

fn assert_fail() {
    assert!(black_box(false));
}

fn panic_fail() {
    panic!("Test failed by panicking");
}

fn unreachable_fail() {
    unreachable!("This should not be reachable");
}

fn zero_divide_fail() {
    black_box(1 / black_box(0));
}

fn abort_fail() {
    std::process::abort();
}

fn main() {
    let mut m = exeter::Manifest::new();

    m.register("nop_pass", nop_pass)
        .set_description("Do nothing");

    m.register("exit_pass", exit_pass)
        .set_description("std::process::exit(0)");

    m.register("assert_pass", assert_pass)
        .set_description("assert!(true)");

    m.register("exit_fail", exit_fail)
        .set_description("Fail by std::process::exit(1)");

    m.register("assert_fail", assert_fail)
        .set_description("Fail by assert!(false)");

    m.register("panic_fail", panic_fail)
        .set_description("Fail by panic!()");

    m.register("unreachable_fail", unreachable_fail)
        .set_description("Fail by unreachable!()");

    m.register("zero_divide_fail", zero_divide_fail)
        .set_description("Fail by division by zero");

    m.register("abort_fail", abort_fail)
        .set_description("Fail by std::process::abort()");

    m.main();
}
