#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

exetool_src = files('exetool')
exetool = find_program(exetool_src)

# Install exetool as a script
install_data(exetool_src, install_dir: get_option('bindir'), install_mode: 'rwxr-xr-x')

# Basic functionality tests
test('exetool/version', exetool, args : ['--version'])
test('exetool/help', exetool, args : ['--help'])

# Negative tests for probe subcommand
test('exetool/probe_no_command', hardfails, args : [exetool, 'probe'])
test('exetool/probe_invalid_cmd', hardfails, args : [exetool, 'probe', '--', 'echo', 'not exeter'])
test('exetool/probe_no_exeter_flag', hardfails, args : [exetool, 'probe', '--', 'ls'])
test('exetool/probe_nonexistent', hardfails, args : [exetool, 'probe', '--', 'nonexistent_command'])

# Test validation of test identifiers
invalid_test_dash = files('../selftest/invalid_test_dash.py')
invalid_test_empty = files('../selftest/invalid_test_empty.py')
test('exetool/list_invalid_dash', hardfails, args : [exetool, 'list', '--', 'python3', invalid_test_dash])
test('exetool/list_invalid_empty', hardfails, args : [exetool, 'list', '--', 'python3', invalid_test_empty])

# Test validation of metadata format
invalid_metadata_key = files('../selftest/invalid_metadata_key.py')
invalid_metadata_empty_line = files('../selftest/invalid_metadata_empty_line.py')
invalid_metadata_no_equals = files('../selftest/invalid_metadata_no_equals.py')
invalid_metadata_empty_key = files('../selftest/invalid_metadata_empty_key.py')
invalid_metadata_incomplete_escape = files('../selftest/invalid_metadata_incomplete_escape.py')
valid_metadata_escapes = files('../selftest/valid_metadata_escapes.py')

test('exetool/metadata_invalid_key', hardfails, args : [exetool, 'metadata', '--', 'python3', invalid_metadata_key, '--', 'test1'])
test('exetool/metadata_invalid_empty_line', hardfails, args : [exetool, 'metadata', '--', 'python3', invalid_metadata_empty_line, '--', 'test1'])
test('exetool/metadata_invalid_no_equals', hardfails, args : [exetool, 'metadata', '--', 'python3', invalid_metadata_no_equals, '--', 'test1'])
test('exetool/metadata_invalid_empty_key', hardfails, args : [exetool, 'metadata', '--', 'python3', invalid_metadata_empty_key, '--', 'test1'])
test('exetool/metadata_invalid_incomplete_escape', hardfails, args : [exetool, 'metadata', '--', 'python3', invalid_metadata_incomplete_escape, '--', 'test1'])
test('exetool/metadata_valid_escapes', exetool, args : ['metadata', '--', 'python3', valid_metadata_escapes, '--', 'test1'])

# Linters
test('exetool/flake8', flake8, args : exetool_src)

test('exetool/mypy', mypy, args : ['--strict', exetool_src])
