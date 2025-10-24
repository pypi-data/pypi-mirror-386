#! /bin/sh
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>
#
# selftest/check_bats_number.sh - Check bats script against list

set -e

LIST="$1"
BATS_SCRIPT="$2"

NUM_LIST="$(wc -l < "$LIST")"
NUM_BATS="$($BATS -c "$BATS_SCRIPT")"

if [ "$NUM_LIST" != "$NUM_BATS" ]; then
    echo "Wrong number of tests in generated BATS script" >&2
    exit 1
fi
