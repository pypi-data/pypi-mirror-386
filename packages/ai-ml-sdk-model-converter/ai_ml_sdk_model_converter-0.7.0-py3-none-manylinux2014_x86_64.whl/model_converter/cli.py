#
# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0
#
import os
import subprocess
import sys


def main():
    binary_name = (
        "model-converter.exe" if sys.platform.startswith("win") else "model-converter"
    )
    binary_path = os.path.join(os.path.dirname(__file__), "binaries/bin", binary_name)
    subprocess.run([binary_path] + sys.argv[1:])
