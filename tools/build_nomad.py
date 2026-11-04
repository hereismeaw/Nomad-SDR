#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build and package RadioMaster Nomad firmware using PlatformIO."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, '-m', 'platformio', 'run', '-d', str(ROOT / 'nomad'),
                '-t', 'package'], check=True)
