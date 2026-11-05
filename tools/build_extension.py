#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build pinned ARC binutils and the CBC-layout-compatible FIFO1 extension."""
import argparse
import hashlib
import json
from pathlib import Path
from common import ROOT, run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--build', type=Path, default=ROOT / 'build')
parser.add_argument('--jobs', type=int, default=4)
parser.add_argument('--binutils-prefix', help='Use existing ARC tools, e.g. /opt/arc/bin/arc-elf-; skips building pinned binutils')
args = parser.parse_args()
build = args.build.resolve()
build.mkdir(parents=True, exist_ok=True)
tools = build / 'arc-binutils'
if args.binutils_prefix:
    assembler, linker, objcopy = (args.binutils_prefix + name for name in ('as', 'ld', 'objcopy'))
else:
    tools.mkdir(parents=True, exist_ok=True)
    if not (tools / 'Makefile').exists():
        run(
            ROOT / 'external/binutils/configure', '--target=arc-elf',
            '--disable-gdb', '--disable-sim', '--disable-gprof', '--disable-nls',
            '--disable-werror', '--without-zstd', '--with-system-zlib', '--disable-shared',
            cwd=tools,
        )
    run('make', '-j', args.jobs, 'MAKEINFO=true', 'all-gas', 'all-ld', 'all-binutils', cwd=tools)
    assembler, linker, objcopy = tools/'gas/as-new', tools/'ld/ld-new', tools/'binutils/objcopy'
out = build / 'lr1121'
out.mkdir(exist_ok=True)
run(assembler, '-mcpu=em4', '-o', out / 'stream.o', 'stream.s',
    cwd=ROOT / 'lr1121/extension')
run(linker, '-T', ROOT / 'lr1121/extension/extension.ld',
    '-o', out / 'stream.elf', out / 'stream.o')
run(objcopy, '-O', 'binary', out / 'stream.elf', out / 'stream.bin')
code = (out / 'stream.bin').read_bytes()
if not 0 < len(code) <= 4080 or any(any(code[i:i+16]) for i in range(240, len(code), 256)):
    raise RuntimeError('Payload size/CBC holes invalid')
print(json.dumps(dict(payload_bytes=len(code), sha256=hashlib.sha256(code).hexdigest())))
