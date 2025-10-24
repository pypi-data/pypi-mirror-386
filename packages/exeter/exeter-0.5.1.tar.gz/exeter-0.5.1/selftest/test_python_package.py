#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#
# Copyright Red Hat
# Author: David Gibson <david@gibson.dropbear.id.au>

"""Test script for Python package installation and functionality"""

import subprocess
import tempfile
import os
import sys


def main() -> int:
    """Test that the Python package can be installed and works correctly"""
    if len(sys.argv) != 2:
        print("Usage: test_python_package.py <version>")
        return 1

    version = sys.argv[1]

    # Create a temporary virtual environment
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = os.path.join(tmpdir, "test_venv")

        # Create virtual environment
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)

        # Get paths for the virtual environment
        if os.name == "nt":
            python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
            pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            python_exe = os.path.join(venv_dir, "bin", "python")
            pip_exe = os.path.join(venv_dir, "bin", "pip")

        # Install the package from wheel (relative to source root)
        source_root = os.environ['MESON_SOURCE_ROOT']
        wheel_path = os.path.join(
            source_root, f"dist/exeter-{version}-py3-none-any.whl"
        )
        subprocess.run([pip_exe, "install", wheel_path], check=True)

        # Test that we can import the exeter module
        subprocess.run([
            python_exe, "-c",
            "import exeter; print('exeter import successful')"
        ], check=True)

        # Test that exetool is available and works
        subprocess.run([
            python_exe, "-c",
            "import subprocess; subprocess.run(['exetool', '--version'], "
            "check=True)"
        ], check=True)

        print("Package installation and functionality test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
