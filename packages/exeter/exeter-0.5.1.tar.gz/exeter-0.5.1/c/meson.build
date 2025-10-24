# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

pkg = import('pkgconfig')

# Check for noreturn support
cc = meson.get_compiler('c')
has_c11_noreturn = cc.compiles('_Noreturn void f(void);', name: '_Noreturn support')
has_gnu_noreturn = cc.has_function_attribute('noreturn')

# Configure header
conf_data = configuration_data()
conf_data.set('HAS_C11_NORETURN', has_c11_noreturn)
conf_data.set('HAS_GNU_NORETURN', has_gnu_noreturn)
config_h = configure_file(
  input: 'config.h.in',
  output: 'config.h',
  configuration: conf_data
)

exeter_srcs = files('exeter.c')
libs = both_libraries('exeter', exeter_srcs)
pkg.generate(libs)

# Examples & tests
trivial = 'trivial.c'
trivial_src = files(trivial)

c_examples = ['example.c', 'registration.c']
example_srcs = files(c_examples)

trivial_shared = executable(fs.stem(trivial), trivial_src,
                            link_with: libs.get_shared_lib())
trivial_static = executable(fs.stem(trivial) + '.static', trivial_src,
                            link_with: libs.get_static_lib())

foreach src : c_examples
  passname = fs.stem(src) + '.pass'
  xpass = fs.exists(passname) ? files(passname) : files()
  failname = fs.stem(src) + '.fail'
  xfail = fs.exists(failname) ? files(failname) : files()
  skipname = fs.stem(src) + '.skip'
  xskip = fs.exists(skipname) ? files(skipname) : files()

  shared = executable(fs.stem(src), src,
                      link_with: libs.get_shared_lib())
  static = executable(fs.stem(src) + '.static', src,
                      link_with: libs.get_static_lib())

  examples += { 'c' / shared.name() : [shared, xpass, xfail, xskip],
                'c' / static.name() : [static, xpass, xfail, xskip] }
endforeach

# Linters
srcs = exeter_srcs + trivial_src + example_srcs

cppcheck = find_program('cppcheck', required : false, disabler : true)
test('c/cppcheck', cppcheck, args : srcs)

clang_tidy = find_program('clang-tidy', required : false, disabler : true)
test('c/clang-tidy', clang_tidy, args : srcs)

# Variables used by the top-level meson.build
trivial_examples += { 'c' / trivial_shared.name() : trivial_shared,
                      'c' / trivial_static.name() : trivial_static }
