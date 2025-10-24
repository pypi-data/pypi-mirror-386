#! /bin/sh

set -e

VENV="$1"

python3 -m venv "$VENV"
$VENV/bin/pip install avocado-framework
