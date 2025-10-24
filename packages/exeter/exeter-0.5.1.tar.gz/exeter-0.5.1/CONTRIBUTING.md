# Contributing to exeter

Submit changes via:
- Email patches to [david@gibson.dropbear.id.au](mailto:david@gibson.dropbear.id.au)
- GitLab [merge requests](https://gitlab.com/dgibson/exeter/-/merge_requests)

## Build System and Testing

Build and test with [Meson](https://mesonbuild.com/):

```bash
meson setup build
meson compile -C build
meson test -C build
```

Please ensure all tests pass before submitting.

## Adding New Language Support

1. Create directory (e.g., `rust/`, `go/`)
2. Implement [exeter protocol](PROTOCOL.md)
3. Provide trivial and additional test examples
4. Add build integration to `meson.build`

## Adding examples

1. Update `.pass` and `.fail` files

## Tests

Tests throughout project structure. Each language has tests plus
there are shared tests in `selftest/`.

All languages must pass "trivial tests" suite.

## Code Style

In general:
- No trailing whitespace except a single newline at end of file
- Use standard libraries only. Keep exeter lightweight and
  self-contained.

### Python

- PEP 8

### C

- Linux Kernel style
- Don't use typedefs for structures or unions

### Shell

- POSIX-compatible

### Markdown

- Wrap before column 80 where possible

## Developer's Certificate of Origin

exeter uses the Linux kernel's "Signed-off-by" process. If you can
certify the below:

    Developer's Certificate of Origin 1.1

    By making a contribution to this project, I certify that:

        (a) The contribution was created in whole or in part by me and I
            have the right to submit it under the open source license
            indicated in the file; or

        (b) The contribution is based upon previous work that, to the best
            of my knowledge, is covered under an appropriate open source
            license and I have the right under that license to submit that
            work with modifications, whether created in whole or in part
            by me, under the same open source license (unless I am
            permitted to submit under a different license), as indicated
            in the file; or

        (c) The contribution was provided directly to me by some other
            person who certified (a), (b) or (c) and I have not modified
            it.

        (d) I understand and agree that this project and the contribution
            are public and that a record of the contribution (including all
            personal information I submit with it, including my sign-off) is
            maintained indefinitely and may be redistributed consistent with
            this project or the open source license(s) involved.

Add this line:

	Signed-off-by: Random J Developer <random@developer.example.org>

`git commit -s` does this automatically. Use your real name (sorry, no
pseudonyms). Any further SoBs (Signed-off-by:'s) following the
author's are from people handling and transporting the patch, but were
not involved in its development. SoB chains should reflect the
**real** route a patch took as it was propagated to the maintainers,
with the first SoB entry signalling primary authorship.


## Code Assistant Contributions

Requirements for AI-assisted contributions:

1. "Co-Authored-By:" line in commit message, with tool and model version:
   ```
   Co-Authored-By: <tool> <tool version> (<model version>)
   ```
2. Only humans add `Reviewed-by:` or `Signed-off-by:`
3. A human must review before merging

`Co-Authored-By` is also used for human co-authors, which is a
downside of this approach.  However `Generated-by`, the mostly widely
used other format, suggests that AI assistance works somewhat like a
more mechanical code generator (e.g. coccinelle, bison).  This doesn't
reflect how an AI assistant is usually guided and edited before
commit.
