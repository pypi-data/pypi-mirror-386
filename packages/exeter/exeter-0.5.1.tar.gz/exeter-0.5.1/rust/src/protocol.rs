// SPDX-License-Identifier: MIT
//
// Copyright Red Hat
// Author: David Gibson <david@gibson.dropbear.id.au>
//

//! Protocol constants and utilities for the exeter test framework
//!
//! This module defines the protocol version, exit codes, and utility functions
//! that implement the exeter test protocol specification.

use std::process;

/// Protocol version supported by this library
///
/// This version string is printed the `--exeter` command line option.
pub const VERSION: &str = "0.4.1";

/// Exit code for successful test completion
pub const EXIT_PASS: i32 = 0;

/// Exit code for skipped tests
pub const EXIT_SKIP: i32 = 77;

/// Exit code for protocol violations and hard failures
///
/// Used internally for exeter protocol errors such as invalid test IDs,
/// duplicate registrations, or other framework-level failures that prevent
/// test execution.
pub const EXIT_HARD_FAILURE: i32 = 99;

/// Skip the current test with the given reason
///
/// This function never returns - it exits the process with code 77
/// according to the exeter protocol.
///
/// # Example
/// ```rust,no_run
/// use exeter::skip;
///
/// fn conditional_test() {
///     if !std::path::Path::new("/proc/version").exists() {
///         skip("Test requires Linux /proc filesystem");
///     }
///     // Test code continues here...
/// }
/// ```
pub fn skip(reason: &str) -> ! {
    println!("SKIP: {}", reason);
    process::exit(EXIT_SKIP);
}
