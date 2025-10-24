# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>
#
# selftest/meson.build - Helper scripts for self testing

# Helper to check for things which should fail
fails = find_program(files('fails'))

# Helper to check for things which should hard fail (status 99)
hardfails = find_program(files('hardfails'))

# Helper to check for things which should skip (status 77)
skips = find_program(files('skips'))

# Locate a suitable Avocado runned
avocado = find_program('avocado',
                       required : false,
                       disabler : true,
                       version : '>=107.0')

# Helper to check Avocado manifest against a plain manifest
check_avocado_list = files('check_avocado_list.sh')

# Locate a suitable BATS runner
bats = find_program('bats',
                    required : false,
                    disabler : true)

# Helper to check BATS script against a plain manifest
check_bats_count = files('check_bats_count.sh')

# Helper to compare lists ignoring order
cmp = find_program('cmp')
checklist = files('checklist.py')

# Special case lists
trivial_pass = files('trivial.pass')
trivial_fail = files('trivial.fail')
trivial_skip = files('trivial.skip')
trivial_list1 = files('trivial.1')
trivial_list2 = files('trivial.2')

# Python linting for selftest scripts
selftest_py_files = files(
  'checklist.py',
  'invalid_metadata_empty_key.py',
  'invalid_metadata_empty_line.py',
  'invalid_metadata_incomplete_escape.py',
  'invalid_metadata_key.py',
  'invalid_metadata_no_equals.py',
  'invalid_test_dash.py',
  'invalid_test_empty.py',
  'test_python_package.py',
  'test_version_consistency.py',
  'valid_metadata_escapes.py'
)

test('selftest/flake8', flake8, args : selftest_py_files)
test('selftest/mypy', mypy, args : ['--strict', selftest_py_files])
