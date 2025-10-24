// SPDX-License-Identifier: MIT
//
// Copyright Red Hat
// Author: David Gibson <david@gibson.dropbear.id.au>
//

//! Test manifest and registration for the exeter test protocol
//!
//! This module provides the [`Manifest`] type which implements the
//! exeter protocol, along with supporting types and functions.

use std::collections::hash_map::Entry;
use std::collections::HashMap;
use std::convert::Infallible;
use std::env;
use std::process;
use std::sync::OnceLock;

use crate::protocol;

/// Global state for tracking current test execution
static CURRENT_TESTID: OnceLock<&'static str> = OnceLock::new();

/// Get the ID of the currently running test
///
/// Returns the test ID if a test is currently running, or None if no test
/// is currently running.
///
/// # Example
/// ```rust,no_run
/// use exeter::current_testid;
///
/// fn my_test() {
///     let test_id = current_testid().expect("Should be running within a test");
///     println!("Currently running test: {}", test_id);
/// }
/// ```
pub fn current_testid() -> Option<&'static str> {
    CURRENT_TESTID.get().copied()
}

pub trait TestFunction: FnOnce() + 'static {}
impl<F: FnOnce() + 'static> TestFunction for F {}

/// A single exeter test case
///
/// Represents a registered test with optional metadata.  Created
/// by [`Manifest::register()`].
pub struct TestCase {
    func: Box<dyn TestFunction>,
    description: Option<String>,
}

impl TestCase {
    fn new<F: TestFunction>(f: F) -> Self {
        Self {
            func: Box::new(f),
            description: None,
        }
    }

    /// Set description for this test case
    ///
    /// The description is included in test metadata and can be used
    /// by test runners for documentation purposes.
    ///
    /// # Example
    /// ```rust,no_run
    /// use exeter::Manifest;
    ///
    /// let mut m = Manifest::new();
    /// let c = m.register("test.id", || {} );
    /// c.set_description("Test description");
    /// m.main();
    /// ```
    pub fn set_description(&mut self, description: &str) {
        self.description = Some(description.to_string());
    }
}

/// Manifest of tests for an exeter executable
///
/// A `Manifest` manages test registration and implements the exeter
/// protocol command-line interface. Create a manifest, register tests
/// with [`Manifest::register()`], then call [`Manifest::main()`] to
/// process command line arguments and execute tests.
///
/// # Example
/// ```rust
/// use exeter::Manifest;
///
/// fn basic_test() {
///     assert_eq!(2 + 2, 4);
/// }
///
/// fn main() {
///     let mut m = Manifest::new();
///     m.register("math.addition", basic_test)
///         .set_description("Basic arithmetic test");
///     m.main(); // Never returns
/// }
/// ```
#[derive(Default)]
pub struct Manifest {
    tests: HashMap<String, TestCase>,
}

impl Manifest {
    /// Create a new manifest
    ///
    /// Returns a [`Manifest`] with no tests.
    pub fn new() -> Self {
        Default::default()
    }

    /// Register a test
    ///
    /// Returns a [`TestCase`] reference which can be used to set
    /// metadata.
    ///
    /// # Panics
    ///
    /// Exits with status code 99 if the test ID is invalid, or
    /// duplicates an already registered test.
    pub fn register<F: TestFunction>(&mut self, id: &str, func: F) -> &mut TestCase {
        validate_test_id(id).unwrap_or_else(|e| {
            eprintln!("Error: {}", e);
            process::exit(protocol::EXIT_HARD_FAILURE);
        });

        let slot = self.tests.entry(id.to_string());
        match slot {
            Entry::Occupied(_) => {
                eprintln!("Error: Duplicate test ID: {}", id);
                process::exit(protocol::EXIT_HARD_FAILURE);
            }
            Entry::Vacant(v) => {
                let c = TestCase::new(func);

                v.insert(c)
            }
        }
    }

    /// Main entry point for exeter test programs
    ///
    /// Implements the exeter test protocol, parsing command line
    /// arguments and executing the appropriate action. It should be
    /// called from your program's main function.
    pub fn main(self) -> ! {
        let args: Vec<String> = env::args().collect();
        let exename = args.first().map(|s| s.as_str()).unwrap_or("exeter-test");

        // Handle no arguments or --help
        if args.len() == 1 || (args.len() == 2 && args[1] == "--help") {
            usage(exename);
            process::exit(protocol::EXIT_PASS);
        }

        match args[1].as_str() {
            "--exeter" => {
                println!("exeter test protocol {}", protocol::VERSION);
            }

            "--list" => {
                if let Err(e) = self.list(&args[2..]) {
                    eprintln!("Error: {}", e);
                    process::exit(protocol::EXIT_HARD_FAILURE);
                }
            }

            "--metadata" => {
                if args.len() != 3 {
                    usage(exename);
                    process::exit(protocol::EXIT_HARD_FAILURE);
                }

                if let Err(e) = self.print_metadata(&args[2]) {
                    eprintln!("Error: {}", e);
                    process::exit(protocol::EXIT_HARD_FAILURE);
                }
            }

            testid => {
                if args.len() != 2 {
                    usage(exename);
                    process::exit(1);
                }

                // Set the current test ID for current_testid() to work
                CURRENT_TESTID
                    .set(testid.to_string().leak())
                    .expect("Race initialising CURRENT_TESTID");

                let Err(e) = self.run(testid);
                eprintln!("Error: {}", e);
                process::exit(protocol::EXIT_HARD_FAILURE);
            }
        }

        process::exit(protocol::EXIT_PASS);
    }

    /// List test cases
    fn list(&self, test_ids: &[String]) -> Result<(), Error> {
        if test_ids.is_empty() {
            // List all tests
            for testid in self.tests.keys() {
                println!("{}", testid);
            }
        } else {
            // List only specified tests
            for testid in test_ids {
                if !self.tests.contains_key(testid) {
                    return Err(Error::TestNotFound(testid.clone()));
                }
                println!("{}", testid);
            }
        }

        Ok(())
    }

    /// Output metadata for a specific test
    fn print_metadata(&self, testid: &str) -> Result<(), Error> {
        let c = self
            .tests
            .get(testid)
            .ok_or_else(|| Error::TestNotFound(testid.to_string()))?;

        // Only output description if it exists, like the C implementation
        if let Some(ref description) = c.description {
            println!("description={}", metadata_escape(description));
        }

        Ok(())
    }

    /// Run a specific test
    fn run(mut self, testid: &str) -> Result<Infallible, Error> {
        let c = self
            .tests
            .remove(testid)
            .ok_or_else(|| Error::TestNotFound(testid.to_string()))?;

        println!("exeter (rust): Running test {}", testid);

        (c.func)();
        std::process::exit(protocol::EXIT_PASS);
    }
}
/// Error types for exeter operations
///
/// Represents all possible errors that can occur during test registration,
/// execution, and metadata operations.
#[derive(Debug)]
enum Error {
    /// Test ID contains invalid characters or is empty
    InvalidTestId(String),
    /// Referenced test ID was not found in the manifest
    TestNotFound(String),
}

impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Error::InvalidTestId(id) => write!(f, "Invalid test ID: {}", id),
            Error::TestNotFound(id) => write!(f, "Test not found: {}", id),
        }
    }
}

impl std::error::Error for Error {}

/// Validate a test ID according to the exeter protocol
fn validate_test_id(testid: &str) -> Result<(), Error> {
    if testid.is_empty() {
        return Err(Error::InvalidTestId("Test ID cannot be empty".to_string()));
    }

    for ch in testid.chars() {
        if !ch.is_alphanumeric() && ch != '.' && ch != ';' && ch != '_' {
            return Err(Error::InvalidTestId(format!(
                "Test ID '{}' contains invalid character '{}'",
                testid, ch
            )));
        }
    }

    Ok(())
}

/// Escape a string value using minimal C-style escape sequences
fn metadata_escape(value: &str) -> String {
    value
        .replace('\\', "\\\\")
        .replace('\n', "\\n")
        .replace('\0', "\\0")
}

/// Print usage information
fn usage(exename: &str) {
    println!("Usage: {} [OPTIONS] <testcase id>", exename);
    println!();
    println!("Exeter (Rust) based tests.");
    println!();
    println!("Options:");
    println!("    --exeter         display protocol version and exit");
    println!("    --help           display this help and exit");
    println!("    --list           list test cases and exit");
    println!("    --metadata <id>  output metadata for test case and exit");
}
