#! /bin/sh
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>
#
# sh/example.sh - Assorted shell examples

. "$(dirname "$0")/exeter.sh"

# Several ways to pass
exeter_register exit_pass exit 0
exeter_set_description exit_pass "exit 0"

exeter_register nop_pass :
exeter_set_description nop_pass "Do nothing (:)"

exeter_register true_pass /bin/true
exeter_set_description true_pass "Call /bin/true"

exeter_register test_pass [ "1" = "1" ]
exeter_set_description test_pass "Test [ \"1\" = \"1\" ]"

# Several ways to fail
exeter_register exit_fail exit 1
exeter_set_description exit_fail "Fail by exit 1"

exeter_register false_fail /bin/false
exeter_set_description false_fail "Call /bin/false"

exeter_register kill_fail kill $$
exeter_set_description kill_fail "Fail by kill \$\$"

exeter_register test_fail [ "1" = "2" ]
exeter_set_description test_fail "Test [ \"1\" = \"2\" ]"

exeter_main "$@"
