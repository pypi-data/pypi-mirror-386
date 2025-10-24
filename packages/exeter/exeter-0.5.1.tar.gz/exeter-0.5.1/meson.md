# Using exeter with Meson

Meson can execute exeter programs directly, running each test as an
individual Meson test.

## Adding Individual Test Cases

Register an individual exeter test ID as a Meson test:

```meson
test('example_test', test_program, args : ['test_case_name'])
```

For interpreted programs:

```meson
py = import('python').find_installation('python3')
test('example_test', py, args : ['test_program.py', 'test_case_name'])
```

## Adding All Test Cases

**Caveat:** This only works for exeter programs which don't need
compilation.  (TODO: Enhance Meson to remove this limitation)

```meson
exetool = find_program('exetool')
test_prog = files('test_program')
test_ids = run_command(exetool, 'list', '--', 'test_prog', check : true).stdout().splitlines()
foreach id : test_ids
  test('test_program' / id, test_prog, args : [ id ])
endforeach
```

## Running Tests

```bash
meson test                      # All tests
meson test example              # Pattern match
meson test --verbose            # Verbose output
```
