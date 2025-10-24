#! /bin/sh
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>
#
# selftest/check_avocado_list.sh - Check avocado json against list

set -e

LIST="$1"
JSON="$2"

NUM_LIST="$(wc -l < "$LIST")"
NUM_AVOCADO="$($AVOCADO list "$JSON" | wc -l)"

if [ "$NUM_LIST" != "$NUM_AVOCADO" ]; then
    echo "Wrong number of tests in generated avocado json" >&2
    exit 1
fi
