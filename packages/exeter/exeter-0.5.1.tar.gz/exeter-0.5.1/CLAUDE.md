# CLAUDE.md

Guidance to Claude Code (claude.ai/code)

## AI Attribution

**IMPORTANT**: AI assisted commits *must* have this in the commit
message.  Always check current tool version (`claude --version`) and
model version.

```
Co-Authored-By: Claude Code <tool-version> (<model-version>)
```

**Never add:**
- `Reviewed-by:`
- `Signed-off-by:`

## Overview

exeter is a test protocol for tests independent of language and
runner. Libraries implement the protocol for several languages (C,
Python, Shell, Rust). Register tests with exeter to create executables
that can run individual tests or generate manifests.

## Build Commands

```bash
meson setup claudebuild
meson compile -C claudebuild
meson test -C claudebuild
```

Use 'claudebuild' to avoid conflicting with concurrent user builds.

Stay in the top level directory.

## Architecture

**Test Protocol**:
- Protocol version: 0.4.1
- Command-line interface: `--exeter`, `--list [test_id ...]`, `--metadata test_id`, `test_id`
- Exit codes: 0=success, 77=skip, 99=hard error, other=failure

**[exetool](exetool/exetool)**:
- CLI tool to work with tests.
- When adding subcommands, also update `exetool/exetool.1` man page and exetool version

**Common Patterns**:
- Test registration via `exeter.register()` (Python),
  `exeter_register()` (C/shell)
- Test IDs are alphanumeric strings with dots, semicolons, underscores

## Documentation

- [Overview](README.md)
- [Test Protocol](PROTOCOL.md)
- [Code Contribution](CONTRIBUTING.md)
- Test Runner Integration
  - [Meson](meson.md)
  - [Avocado](avocado.md)
  - [BATS](bats.md)
- [exetool man page](exetool/exetool.1)

When modified also update `CLAUDE.md` to match.

## Testing

Self testing via Meson:
- "trivial tests" are common across all supported languages
- Additional tests validate language-specific features and idioms.
- Cross-validate different manifest formats (Avocado, BATS, plain)
- Validate that we properly report failing test cases.
- Validate integration with external runners


## Code Style and Conventions

In general:
- No trailing whitespace except a single newline at end of file
- Use standard libraries only. Keep exeter lightweight and
  self-contained.
- Prefer 'c' as the local variable name for testcase objects
- Prefer short names for local variables.

### Python

- PEP 8
- Full type annotations
  - Prefer <type> | None to Optional[<type>]

### C

- Linux Kernel style
- Don't use typedefs for structures or unions

### Shell

- POSIX-compatible

### Rust

- Rust code is compiled and tested using meson's built in support,
  rather than cargo
- Follow standard Rust conventions (rustfmt, clippy)

### Markdown

- Wrap before column 80 where possible

## Development Workflow

- Aim for similar test coverage across all languages
- Update `.pass` and `.fail` files when changing test examples
- Run full test suite to verify cross-language compatibility
- Test both direct execution and runner integration
- List generated files in `.gitignore`
