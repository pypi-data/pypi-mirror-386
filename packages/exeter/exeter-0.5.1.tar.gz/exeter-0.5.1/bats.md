# Using exeter with BATS

[BATS](https://github.com/bats-core/bats-core) can execute exeter
tests via scripts from `exetool bats`.

## Setup

Install per [BATS docs](https://bats-core.readthedocs.io/en/stable/installation.html):

```bash
sudo apt install bats        # Ubuntu/Debian
sudo dnf install bats        # Fedora
brew install bats-core       # macOS
```

## Generate Scripts

```bash
# Generate BATS script for all tests
exetool bats -- ./example.py > tests.bats

# Generate BATS script for specific tests
exetool bats -- ./example.py -- test1 test2 > subset.bats
```

## Run Tests

```bash
bats tests.bats
```

BATS test names use the test description from metadata when available,
otherwise the exeter test ID.  Certain characters are replace with
underscores, because they seem to be problematic, even when quoted for
the shell.  I haven't managed to find documentation on what is and
isn't safe, so for now we replace: [], {}, $, `, ', ", \n, \r and \t.

See [BATS docs](https://bats-core.readthedocs.io/) for more options.
