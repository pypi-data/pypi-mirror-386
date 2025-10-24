#! /bin/sh
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

. $(dirname $0)/exeter.sh

exeter_register trivial_pass true
exeter_set_description trivial_pass "Trivially pass"
exeter_register trivial_fail false
exeter_set_description trivial_fail "Trivially fail"
exeter_register trivial_skip exeter_skip "This test is trivially skipped"
exeter_set_description trivial_skip "Trivially skip"

exeter_main "$@"

