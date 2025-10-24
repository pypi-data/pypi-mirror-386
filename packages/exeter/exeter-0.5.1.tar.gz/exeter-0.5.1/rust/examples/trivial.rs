// SPDX-License-Identifier: MIT
//
// Copyright Red Hat
// Author: David Gibson <david@gibson.dropbear.id.au>

//! Trivial exeter tests in Rust

fn trivial_pass() {
    // Do nothing - should pass
}

fn trivial_fail() {
    // Fail by panicking
    panic!("Trivial failure");
}

fn trivial_skip() {
    exeter::skip("This test is trivially skipped");
}

fn main() {
    let mut m = exeter::Manifest::new();

    m.register("trivial_pass", trivial_pass)
        .set_description("Trivially pass");

    m.register("trivial_fail", trivial_fail)
        .set_description("Trivially fail");

    m.register("trivial_skip", trivial_skip)
        .set_description("Trivially skip");

    m.main();
}
