# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

project(
  'exeter',
  license: 'MIT',
  license_files: 'MIT.txt',
  version: '0.5.1',
  meson_version: '>=1.6.0',
  default_options : [ 'werror=true' ],
)

fs = import('fs')

# Python linting tools
flake8 = find_program('flake8', required : false, disabler : true)
mypy = find_program('mypy', required : false, disabler : true)

langs = []
if get_option('build_python')
  langs += ['py3']
endif
if get_option('build_shell')
  langs += ['sh']
endif
if get_option('build_c')
  langs += ['c']
  add_languages('c', required: true)
endif
if get_option('build_rust')
  langs += ['rust']
  add_languages('rust', required: true)
endif

subdir('selftest')
subdir('exetool')

trivial_examples = {}
examples = {}

foreach lang : langs
  subdir(lang)
endforeach

lists = {}
jsons = {}
batsfiles = {}

# Expected output for --exeter option
protocol_md = files('PROTOCOL.md')
exeter_expected = custom_target('exeter.expected',
                                command : ['grep', '-o', '-m', '1', 'exeter test protocol [0-9.]*', protocol_md],
                                capture : true,
                                output : 'exeter.expected',
                                depend_files : protocol_md
                               )

# Tests that make sense for every example, even if it has failing tests
foreach name, example : trivial_examples
  examples += { name: [example, trivial_pass, trivial_fail, trivial_skip] }
endforeach

foreach name, info : examples
  message(name)
  example = info[0]
  xpass = info[1]
  xfail = info[2]
  xskip = info[3]

  # --exeter option tests
  test('exeter|' + name, example, args : ['--exeter'])
  exeterpath = name.underscorify() + '.exeter'
  exeter_output = custom_target(exeterpath,
                                command : [example, '--exeter'],
                                capture : true,
                                output : exeterpath,
                                build_always_stale : true, # FIXME
                               )
  test('exeter_output|' + name, cmp, args : [exeter_output, exeter_expected])

  # Help output
  test('noargs|' + name, example)
  test('help|' + name, example, args : ['--help'])

  # Test that generating the manifests doesn't error out
  test('list|' + name, example, args : ['--list'])
  test('probe|' + name, exetool, args : ['probe', '--', example])
  test('avocado|' + name, exetool, args : ['avocado', '--', example])
  test('bats|' + name, exetool, args : ['bats', '--', example])

  # Targets for the manifests
  listpath = name.underscorify() + '.list'
  lists += { name : custom_target(listpath,
                                  command : [example, '--list'],
                                  capture : true,
                                  output : listpath,
                                  build_always_stale : true, # FIXME
                                  ) }

  jsonpath = name.underscorify() + '.json'
  jsons += { name : custom_target(jsonpath,
                                  command : [exetool, 'avocado', '--', example],
                                  capture : true,
                                  output : jsonpath,
                                  build_always_stale : true, # FIXME
                                 ) }

  batspath = name.underscorify() + '.bats'
  batsfiles += { name : custom_target(batspath,
                                      command : [exetool, 'bats', '--', example],
                                      capture : true,
                                      output : batspath,
                                      build_always_stale : true, # FIXME
                                     ) }

  # Compare list to expected contents
  test('list|' + name, checklist, args : [lists[name], xpass, xfail, xskip])

  # Validate exetool list output matches direct --list
  exetool_listpath = name.underscorify() + '.exetool.list'
  exetool_lists = custom_target(exetool_listpath,
                               command : [exetool, 'list', '--', example],
                               capture : true,
                               output : exetool_listpath,
                               build_always_stale : true) # FIXME
  test('exetool_vs_list|' + name, checklist, args : [exetool_lists, lists[name]])

  # Sanity check the Avocado manifest against the plain list
  if avocado.found()
    test('avocado_vs_list|' + name, check_avocado_list,
	 args : [lists[name], jsons[name]],
	 env : {'AVOCADO' : avocado.full_path()})
  endif

  # Sanity check the BATS script against the plain list
  if bats.found()
    test('bats_vs_list|' + name, check_bats_count,
	 args : [lists[name], batsfiles[name]],
	 env : {'BATS' : bats.full_path()})
  endif

  # Run each passing case in the example as a meson test case
  passcases = []
  foreach list : xpass
    passcases += fs.read(list).splitlines()
  endforeach
  foreach case : passcases
    test(name + '|' + case, example, args : [case])
  endforeach

  # Check for failuer on each failing case as a meson test case
  failcases = []
  foreach list : xfail
    failcases += fs.read(list).splitlines()
  endforeach
  foreach case : failcases
    test(name + '|' + case, fails, args : [example, case])
  endforeach

  # Check for skip on each skipping case as a meson test case
  skipcases = []
  foreach list : xskip
    skipcases += fs.read(list).splitlines()
  endforeach
  foreach case : skipcases
    test(name + '|' + case, skips, args : [example, case])
  endforeach

  # Validate metadata output for all test cases (pass, fail, and skip)
  allcases = passcases + failcases + skipcases
  foreach case : allcases
    test('metadata|' + name + '|' + case, exetool, args : ['metadata', '--', example, '--', case])
  endforeach

  # Check we get the expected results running via avocado
  passjsonpath = name.underscorify() + '.pass.json'
  passjson = custom_target(passjsonpath,
                           command : [exetool, 'avocado', '--', example, '--'] + passcases + skipcases,
                           capture : true,
                           output : passjsonpath,
                           build_always_stale : true, # FIXME
                          )
  
  test('avocado_run|' + name, avocado, args : ['run', passjson])

  # Check we get the expected results running via bats
  passbatspath = name.underscorify() + '.pass.bats'
  passbats = custom_target(passbatspath,
                           command : [exetool, 'bats', '--', example, '--'] + passcases + skipcases,
                           capture : true,
                           output : passbatspath,
                           build_always_stale : true, # FIXME
                          )
  
  test('bats_run|' + name, bats, args : [passbats])

  # Check running the tests via avocado fails
  foreach case : failcases
    failjsonpath = name.underscorify() + '.' + case +'.fail.json'
    failjson = custom_target(failjsonpath,
                             command : [exetool, 'avocado', '--', example, '--', case],
                             capture : true,
                             output : failjsonpath,
                             build_always_stale : true, # FIXME
                            )
    test('avocado_run_fail|' + name + '|' + case, fails, args : [avocado.full_path(), 'run', failjson])
  endforeach

  # Check running the tests via bats fails
  foreach case : failcases
    failbatspath = name.underscorify() + '.' + case +'.fail.bats'
    failbats = custom_target(failbatspath,
                             command : [exetool, 'bats', '--', example, '--', case],
                             capture : true,
                             output : failbatspath,
                             build_always_stale : true, # FIXME
                            )
    test('bats_run_fail|' + name + '|' + case, fails, args : [bats.full_path(), failbats])
  endforeach
endforeach

foreach name, example : trivial_examples
  # Make sure we can have passing, failing, and skipping tests
  test('trivial_pass|' + name, example, args : ['trivial_pass'])
  test('trivial_fail|' + name, fails, args : [example, 'trivial_fail'])
  test('trivial_skip|' + name, skips, args : [example, 'trivial_skip'])

  # Special cases for listing
  listpath = name.underscorify() + '.1'
  list1 = custom_target(listpath,
                        command : [example, '--list', 'trivial_pass'],
                        capture : true,
                        output : listpath,
                        build_always_stale : true, # FIXME
                       )
  test('list1|' + name, cmp, args : [list1, trivial_list1])

  jsonpath = name.underscorify() + '.1.json'
  json1 = custom_target(jsonpath,
                        command : [exetool, 'avocado', '--', example, '--', 'trivial_pass'],
                        capture : true,
                        output : jsonpath,
                        build_always_stale : true, # FIXME
                       )
  # Sanity check the Avocado manifest against the plain list
  if avocado.found()
    test('avocado_vs_list1|' + name, check_avocado_list,
	 args : [trivial_list1, json1],
	 env : {'AVOCADO' : avocado.full_path()})
  endif

  batspath = name.underscorify() + '.1.bats'
  bats1 = custom_target(batspath,
                        command : [exetool, 'bats', '--', example, '--', 'trivial_pass'],
                        capture : true,
                        output : batspath,
                        build_always_stale : true, # FIXME
                       )
  # Sanity check the BATS script against the plain list
  if bats.found()
    test('bats_vs_list1|' + name, check_bats_count,
	 args : [trivial_list1, bats1],
	 env : {'BATS' : bats.full_path()})
  endif

  listpath = name.underscorify() + '.2'
  list2 = custom_target(listpath,
                        command : [example, '--list', 'trivial_pass', 'trivial_fail'],
                        capture : true,
                        output : listpath,
                        build_always_stale : true, # FIXME
                       )
  test('list2|' + name, cmp, args : [list2, trivial_list2])

  jsonpath = name.underscorify() + '.2.json'
  json2 = custom_target(jsonpath,
                        command : [exetool, 'avocado', '--', example, '--', 'trivial_pass', 'trivial_fail'],
                        capture : true,
                        output : jsonpath,
                        build_always_stale : true, # FIXME
                       )
  # Sanity check the Avocado manifest against the plain list
  if avocado.found()
    test('avocado_vs_list2|' + name, check_avocado_list,
	 args : [trivial_list2, json2],
	 env : {'AVOCADO' : avocado.full_path()})
  endif

  batspath = name.underscorify() + '.2.bats'
  bats2 = custom_target(batspath,
                        command : [exetool, 'bats', '--', example, '--', 'trivial_pass', 'trivial_fail'],
                        capture : true,
                        output : batspath,
                        build_always_stale : true, # FIXME
                       )
  # Sanity check the BATS script against the plain list
  if bats.found()
    test('bats_vs_list2|' + name, check_bats_count,
	 args : [trivial_list2, bats2],
	 env : {'BATS' : bats.full_path()})
  endif
  
  # Make sure we get a hard error on exeter internal errors
  test('list_nonexistent|' + name, hardfails, args : [example, '--list', 'nonexistent'])
  test('nonexistent|' + name, hardfails, args : [example, 'nonexistent'])

  # Validate metadata content for trivial tests
  trivial_pass_metadata_expected = files('selftest/trivial_pass.metadata')
  trivial_fail_metadata_expected = files('selftest/trivial_fail.metadata')

  # Test that trivial_pass metadata matches expected content
  pass_metadata_path = name.underscorify() + '.trivial_pass.metadata'
  pass_metadata = custom_target(pass_metadata_path,
                                command : [example, '--metadata', 'trivial_pass'],
                                capture : true,
                                output : pass_metadata_path,
                                build_always_stale : true
                               )
  test('metadata_content|' + name + '|trivial_pass', cmp, args : [pass_metadata, trivial_pass_metadata_expected])

  # Test that trivial_fail metadata matches expected content
  fail_metadata_path = name.underscorify() + '.trivial_fail.metadata'
  fail_metadata = custom_target(fail_metadata_path,
                                command : [example, '--metadata', 'trivial_fail'],
                                capture : true,
                                output : fail_metadata_path,
                                build_always_stale : true
                               )
  test('metadata_content|' + name + '|trivial_fail', cmp, args : [fail_metadata, trivial_fail_metadata_expected])

  # Validate description content for trivial tests
  trivial_pass_desc_expected = files('selftest/trivial_pass.desc')
  trivial_fail_desc_expected = files('selftest/trivial_fail.desc')

  # Test that trivial_pass description matches expected content
  pass_desc_path = name.underscorify() + '.trivial_pass.desc'
  pass_desc = custom_target(pass_desc_path,
                            command : [exetool, 'desc', '--', example, '--', 'trivial_pass'],
                            capture : true,
                            output : pass_desc_path,
                            build_always_stale : true
                           )
  test('exetool_desc|' + name + '|trivial_pass', cmp, args : [pass_desc, trivial_pass_desc_expected])

  # Test that trivial_fail description matches expected content
  fail_desc_path = name.underscorify() + '.trivial_fail.desc'
  fail_desc = custom_target(fail_desc_path,
                            command : [exetool, 'desc', '--', example, '--', 'trivial_fail'],
                            capture : true,
                            output : fail_desc_path,
                            build_always_stale : true
                           )
  test('exetool_desc|' + name + '|trivial_fail', cmp, args : [fail_desc, trivial_fail_desc_expected])
endforeach

# Python package tests (optional - requires build module)
test_python_package = files('selftest/test_python_package.py')

# Check if build module is available
build_available = run_command(py, '-c', 'import build', check: false)
if build_available.returncode() == 0
  # Test building the Python package
  test('python_package_build', py,
       args: ['-m', 'build', '--sdist', '--wheel'],
       workdir: meson.project_source_root(),
       timeout: 120)

  # Test package can be installed locally
  test('python_package_install_test', test_python_package,
       args: [meson.project_version()],
       env: {'MESON_SOURCE_ROOT': meson.project_source_root()},
       timeout: 180)
else
  message('Skipping Python package tests - build module not available')
endif

# Version consistency test
version_test_script = files('selftest/test_version_consistency.py')
test('version_consistency', version_test_script,
     args: [meson.project_version(), exetool.full_path()])
