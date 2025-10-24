# EXEcutable TestER (exeter)

A test protocol and library collection for language-independent testing.

## Overview


exeter is a test protocol allowing tests to be written in any
language, then run with a variety of testing tools. Unlike TAP, it
prioritises parallel execution and stable test IDs.

Libraries for several languages implement the protocol in a way
natural for the language. Register tests with exeter to create
executables that can run individual tests or generate
manifests. Frameworks like
[Avocado](https://avocado-framework.github.io/) or
[Meson](https://mesonbuild.com/Unit-tests.html) then execute and
collate results.

This separates test language choice from test runner choice. Write
tests in the most convenient language for each case whilst maintaining
unified results. Debug individual tests without framework overhead.

## Why exeter?

**vs Language-specific runners:**
- Poor support for multi-language projects
- Often limited support for test matrices

**vs other frameworks:**
- May impose unnatural styles (e.g. Java-isms in other languages)
- May require unpleasant DSLs for matrices

**vs TAP:**
- Sequential execution (parallel is possible, but awkward)
  - Encourages test inter-dependency
- Numeric test IDs that change
- Difficult to debug a single test

**exeter advantages:**
- Language independence
- Natural syntax per language
- Individual test execution
  - With minimal overhead
- Programmatic test matrices
  - In your language of choice
- Parallel execution by design

## How it works

1. Write tests using exeter libraries
2. Register tests to create an executable
3. Run executable manually, OR
4. Generate manifest for a test runner (Avocado, Meson, etc.)

exeter focuses on test creation, not execution or collation.

## Languages

- [Python 3](py3/) (requires Python 3.11+)
- [Shell](sh/)
- [C](c/)
- [Rust](rust/)

All provide the same test runner interface but prioritise
language-specific patterns over identical test-writing APIs.

## Test runners

Can work with any framework that executes commands.  Specific
information on some common runners:

- [Meson](meson.md)
- [Avocado](avocado.md)
- [BATS](bats.md)

## Further information

Presentation slides from Everything Open 2025:
[gitlab.com/dgibson/eo2025](https://gitlab.com/dgibson/eo2025)

## Trivia

It's named after [here](https://maps.app.goo.gl/RQs5Tg9YMoRbeDRG6),
not [here](https://maps.app.goo.gl/55fw7YvtBfHiorF6A).

## Author

Copyright Red Hat

Written by David Gibson <david@gibson.dropbear.id.au>

Distributed under the [MIT License](MIT.txt).
