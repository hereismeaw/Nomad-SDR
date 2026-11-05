#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Receive-only hardware smoke of USB/TCP -> rtl_tcp, including a retune.

Uses a temporary loopback port. Does not change SDR GUI settings.
"""
import argparse
import json
from pathlib import Path
import socket
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'host'))
from nomad_rtl_tcp import COMMAND, DONGLE_HEADER, serve
from frequency import valid_frequency


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    endpoint = parser.add_mutually_exclusive_group(required=True)
    endpoint.add_argument('--serial')
    endpoint.add_argument('--host')
    parser.add_argument('--radio', type=int, choices=(0, 1), default=0)
    parser.add_argument('--packed-verification',type=Path)
    parser.add_argument('--seconds', type=float, default=60)
    parser.add_argument('--frequency',type=int,default=915000000)
    parser.add_argument('--retune-frequency',type=int,default=245000000)
    parser.add_argument('--report', type=Path, default=Path('build/live-smoke.json'))
    args = parser.parse_args()
    if args.seconds < 10:
        parser.error('Use at least 10 seconds to include setup and retune')
    if not valid_frequency(args.frequency) or not valid_frequency(args.retune_frequency):
        parser.error('Both frequencies must be within 150..2500 MHz')
    ready, stop = threading.Event(), threading.Event()
    ports = []
    def on_ready(port):
        ports.append(port)
        ready.set()
    thread = threading.Thread(target=serve, kwargs=dict(
        host=args.host, serial=args.serial, radio=args.radio, port=0,frequency=args.frequency,
        report=args.report, ready=on_ready, stop=stop,packed_verification=args.packed_verification), daemon=True)
    thread.start()
    total = 0
    gaps = []
    try:
        if not ready.wait(5):
            raise RuntimeError('Proxy did not start')
        with socket.create_connection(('127.0.0.1', ports[0]), timeout=10) as client:
            header = bytearray()
            while len(header) < len(DONGLE_HEADER):
                chunk = client.recv(len(DONGLE_HEADER)-len(header))
                if not chunk:
                    raise RuntimeError('Proxy closed before RTL header')
                header.extend(chunk)
            if header != DONGLE_HEADER:
                raise RuntimeError('Invalid RTL header')
            start = last = time.monotonic()
            retuned = False
            while time.monotonic()-start < args.seconds:
                if not retuned and time.monotonic()-start >= args.seconds/2:
                    client.sendall(COMMAND.pack(1, args.retune_frequency))
                    retuned = True
                chunk = client.recv(65536)
                if not chunk:
                    raise RuntimeError('Proxy closed during acquisition')
                current = time.monotonic()
                gaps.append(current-last)
                last = current
                total += len(chunk)
    finally:
        stop.set()
        thread.join(10)
    if thread.is_alive():
        raise RuntimeError('Proxy failed to stop')
    report = json.loads(args.report.read_text(encoding='utf-8'))
    report['smoke'] = dict(bytes=total, seconds=args.seconds,
                           max_output_gap_ms=1000*max(gaps, default=0))
    args.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    if report['error'] or len(report['jobs']) < 2 or total < args.seconds*250000:
        raise RuntimeError('Smoke failed: inspect report for error, retune, or low throughput')
    for job in report['jobs']:
        terminal = job.get('terminal')
        if not terminal or terminal['flags'] != 4 or terminal['lost_samples']:
            raise RuntimeError('Smoke failed: acquisition did not cancel cleanly')


if __name__ == '__main__':
    main()
