// SPDX-License-Identifier: MIT
//
// Copyright Red Hat
// Author: David Gibson <david@gibson.dropbear.id.au>
//

//! Rust library for the exeter test protocol
//!
//! This library implements the [exeter test
//! protocol](https://gitlab.com/dgibson/exeter/-/blob/main/PROTOCOL.md).
//!
//! ## Quick Start
//!
//! ```rust
//! use exeter::Manifest;
//!
//! fn my_test() {
//!     assert_eq!(2 + 2, 4);
//! }
//!
//! fn main() {
//!     let mut manifest = Manifest::new();
//!     manifest.register("math.addition", my_test)
//!         .set_description("Test basic addition");
//!     manifest.main();
//! }
//! ```
//!
//! ## Rust Test Patterns
//!
//! Test functions follow standard Rust conventions:
//! - Return normally for success
//! - Panic (via `assert!`, `panic!`, etc.) for failure
//! - Call [`exeter::skip()`] to skip a test
//!
//! Use [`current_testid()`] within tests to get the running test ID.
//!
//! ## See also
//!
//! See <https://gitlab.com/dgibson/exeter> for exeter documentation,
//! including test runner integration, and examples in other
//! languages.

pub mod manifest;
pub mod protocol;

pub use manifest::{current_testid, Manifest};
pub use protocol::skip;
