#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

py = import('python').find_installation('python3', pure: true)

subdir('exeter')

py.install_sources(exeter_srcs, subdir: 'exeter')

lintpkgs = exeter_srcs

# Examples & tests
trivial_name = 'trivial.py'
trivial_src = files(trivial_name)
lintpkgs += trivial_src

lintpkgs += files('common.py', 'subexample.py')

py3_examples = ['example.py', 'assert_helpers.py', 'scenario.py', 'testid.py', 'registration.py', 'signals.py']
example_srcs = files(py3_examples)
lintpkgs += example_srcs

# Linters
test('py3/flake8', flake8, args : lintpkgs)

#pylint = find_program('pylint', required : false, disabler : true)
#test('py3/pylint', pylint, args : lintpkgs)

test('py3/mypy', mypy, args : ['--strict', lintpkgs])

# Variables used by the top-level meson.build
trivial_examples += { 'py3' / trivial_name : trivial_src }

foreach name : py3_examples
  passname = fs.stem(name) + '.pass'
  xpass = fs.exists(passname) ? files(passname) : files()
  failname = fs.stem(name) + '.fail'
  xfail = fs.exists(failname) ? files(failname) : files()
  skipname = fs.stem(name) + '.skip'
  xskip = fs.exists(skipname) ? files(skipname) : files()
  examples += { 'py3' / name : [files(name), xpass, xfail, xskip] }
endforeach
