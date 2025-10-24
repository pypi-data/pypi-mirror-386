# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

rust = import('rust')
rustfmt = find_program('rustfmt', required: false, disabler: true)

edition = ['--edition=2021']
crate_name = ['--crate-name', 'exeter']
exeter_srcs = files('src/lib.rs', 'src/manifest.rs', 'src/protocol.rs')

# The library itself
exeter_lib = static_library('exeter', exeter_srcs,
                            rust_args: edition)
exeter_extern = ['--extern', 'exeter=' + exeter_lib.full_path()]

trivial_src = files('examples/trivial.rs')
example_srcs = [trivial_src]

# Exeter binaries and tests

trivial = executable('trivial', trivial_src,
                     link_with : exeter_lib, rust_args: edition)
trivial_examples += { 'rust/trivial' : trivial }
example_srcs = [trivial_src]


foreach name : ['example', 'testid', 'registration']
  src = files('examples' / name + '.rs')
  example_srcs += src
  exe = executable(name, src,
                   link_with : exeter_lib,
                   rust_args: edition)

  passname = name + '.pass'
  xpass = fs.exists(passname) ? files(passname) : files()
  failname = name + '.fail'
  xfail = fs.exists(failname) ? files(failname) : files()
  skipname = name + '.skip'
  xskip = fs.exists(skipname) ? files(skipname) : files()

  examples += { 'rust/' + name : [exe, xpass, xfail, xskip] }
endforeach

# Rust runner unit tests
#rust.test('rust/unit_tests', exeter_lib)

# Rust doctests
rustdoc = find_program('rustdoc', required: false, disabler : true)

# To check library invoke on lib.rs, it finds the rest
test('rust/doctests/exeter', rustdoc,
     args: ['--test', edition, exeter_extern, exeter_srcs[0]],
     workdir: meson.current_source_dir(),
     depends: exeter_lib)

foreach src : example_srcs
  test('rust/doctests/' + fs.name(src), rustdoc,
       args: ['--test', edition, exeter_extern, src],
       workdir: meson.current_source_dir(),
       depends: exeter_lib)
endforeach

# Documentation generation
doc_target = custom_target('rust-doc',
                           command: [rustdoc, edition, crate_name, exeter_extern,
                                    '--output', '@OUTDIR@', exeter_srcs[0]],
                           output: ['doc'],
                           depends: exeter_lib,
                           build_by_default: true,
                           install: true,
                           install_dir: get_option('datadir') / 'doc' / 'exeter' / 'rust')

# Linting / formatting
test('rust/fmt', rustfmt,
     args: ['--check', exeter_srcs, example_srcs])
