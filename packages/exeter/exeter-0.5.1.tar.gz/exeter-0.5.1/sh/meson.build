# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

exeter_srcs = files('exeter.sh')

# Examples & tests
trivial_name = 'trivial.sh'
trivial_src = files(trivial_name)

sh_examples = [ 'example.sh' ]

# Variables used by the top-level meson.build
trivial_examples += { 'sh' / trivial_name : trivial_src }

foreach name : sh_examples
  passname = fs.stem(name) + '.pass'
  xpass = fs.exists(passname) ? files(passname) : files()
  failname = fs.stem(name) + '.fail'
  xfail = fs.exists(failname) ? files(failname) : files()
  skipname = fs.stem(name) + '.skip'
  xskip = fs.exists(skipname) ? files(skipname) : files()
  examples += { 'sh' / name : [files(name), xpass, xfail, xskip] }
endforeach
