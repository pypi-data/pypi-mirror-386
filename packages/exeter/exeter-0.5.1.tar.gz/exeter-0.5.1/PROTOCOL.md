# Exeter Test Protocol

A language-independent command-line interface for test execution by
external runners. Each implementation provides a uniform interface for
listing, executing, and generating metadata about test cases.

## Definitions

**Test program**: A program which implements the exeter test protocol.
Test programs contain one or more test cases and respond to the
standardised command-line interface defined in this protocol.

**Test runner**: A tool which invokes test programs to discover, list,
and/or execute tests. Examples include meson, avocado, and BATS.

**exetool**: A command line tool which works with exeter test programs
to generate test manifests and perform other operations.

**Test ID**: A unique identifier for a test case within a test
program.  Test IDs MUST be non-empty and consist only of alphanumeric
characters, dots (.), semicolons (;), and underscores (_).

## Protocol Version

Protocol versions use semantic versioning (semver).

Current version: **0.4.1**

## Requirements for Test Programs

### Command-Line Interface

All test programs MUST support these command-line options:

- `--exeter`: Display protocol version and exit
- `--list [test_id ...]`: List test identifiers and exit
- `--metadata test_id`: Output metadata for specified test and exit
- `test_id`: Execute specified test

### Exit Codes

Test programs MUST use these exit codes:

- **0**: Success
- **77**: Skip
- **99**: Hard error (includes protocol violations)
- **other**: Test failure

### --exeter

When invoked with `--exeter` a test program MUST output exactly:
```
exeter test protocol 0.4.1
```

This must be UTF-8 encoded (which is equivalent to ASCII in this
case).

### --list

When invoked with `--list` a test program MUST output test IDs, one
per line.  These must be UTF-8 encoded (which is equivalent to ASCII
for test IDs).

If given no further arguments all cases supplied by the test program
MUST be listed.  Otherwise it MUST list only the given tests, or exit
99 if any given IDs are not supplied by the test program.

The test program MUST NOT list any duplicate test IDs.

### --metadata

When invoked with `--metadata test_id` a test program MUST output
metadata for the specified test.  It MUST exit with status 99 if it
does not contain the specified test_id.

- The metadata MUST be formatted as one `key=value` pair per line.
- The test program MUST NOT emit empty lines
- Keys MUST only include alphanumerics, dots (.), semicolons (;),
  underscores (_)
- Keys MUST be non-empty
- All output MUST be UTF-8 encoded

Values use minimal C-style escape sequences.  Test programs MUST
escape: `\\` → `\\\\`, `\n` → `\\n`, `\0` → `\\0`

Test programs SHOULD only include key values defined below.

- **description**: Short (one line) human-readable description of the
  test

**Example:**
```
description=Multi-line test\\nwith details
tags=smoke,regression
timeout=30
```

## Requirements for Test Runners

Test runners MUST:
- Invoke test programs only with arguments described in the protocol

Test runners SHOULD:
- Use exetool to generate test manifests rather than directly invoking
  the test program.
- Handle all defined exit codes appropriately

When invoking test programs with `--metadata` test runners SHOULD:
- Report an error if the metadata has an invalid format
- Decode any standard C escapes in the value, including `\\n`, `\\t`,
  `\\r`, `\\\\`, `\\'`, `\\"`, `\\0`, `\\a`, `\\b`, `\\f`, `\\v`,
  `\\xHH`, `\\NNN`
- Treat invalid escape sequences as literal backslash plus character

## Version History

### 0.4.1
- Added `description` metadata key

### 0.4.0
- Added `--metadata test_id` command for test metadata output
- Defined key-value format with C-style escape sequences
- Keys follow same rules as test IDs

### 0.3.0
- **BREAKING**: Changed test ID validation to allow any position to contain any valid character (alphanumeric, dots, semicolons, underscores)
- **BREAKING**: Added requirement that test IDs must be non-empty

### 0.2.0
- **BREAKING**: Removed `--avocado` from protocol (use `exetool
  avocado` instead)

### 0.1.0
- Initial specification
