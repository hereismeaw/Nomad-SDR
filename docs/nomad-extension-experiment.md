# Nomad: LR1121 custom-code experiment

Hardware experiment performed 2026-11-05 on **radio 1 only** through COM3.
The initial experiment used main ESP32 firmware nomad-0.9.2. Radio 0 remains
the stock baseline. Firmware 0.10.0 subsequently adds [continuous packed streaming](packed-stream.md).

## Result

The existing CBC-oracle/ARC extension route in this repository now works on
the Nomad ESP32 bridge. This experiment used transceiver 0x0103 and the existing
FIFO1 payload; it did not test a new CVE-2026-6232 exploit or a new firmware family.

- Repeated oracle probes returned identical 16-byte results without flashing.
- Forged image plaintext checks passed. The original stock encrypted prefix was
  retained, with the custom extension appended to the application image.
- Application flashing completed. Bootloader identity before and after was
  `22df2100`; application identity remained `22030103`.
- Callback self-test returned IQP3 and FIFO1 markers and restored its callback.
- **Actual code running on LR1121** packed 250 known signed components into
  8-bit and 12-bit formats; every output byte matched the host reference.
- RF snapshot at **915 MHz** returned 8 consecutive banks / 1000 complex samples.
- RF snapshot at **2440 MHz** returned 9 consecutive banks / 1125 complex samples.
- Snapshots use native **62500 S/s**, adaptive 8-bit packing in the radio and
  decode to cf32 on the PC. No RF reference tone was used.
- After resetting radio 1, the normal USB LID8 path completed 8 seconds at
  915 MHz: 250000 samples, flags 0, lost samples 0, maximum queue 3.

This proves custom execution, signed packing and short packed RF capture.
It does not prove indefinite packed streaming, FIFO hardware service throughput,
calibrated RF sensitivity, or 250/500 kS/s on the ESP32. The FIFO1 marker is a
callback test result, not a sustained-transfer benchmark.

## Current hardware state

Radio 1 has the custom application installed. Resetting removes the active RAM
hooks/ring and restores normal operation; it does not remove the flash extension.
Both stock and extended applications identify as `22030103`, so that identity
alone does not distinguish them. The experiment validates the per-chip UID
against the installer verification report before invoking the flash callback.
Radio 0 was not flashed. No bootloader updater was used.

The probe resets the selected radio on success or failure. Normal receive commands
still work, as checked above. Fan and RGB remain in automatic mode.

## Files and reproducibility

All generated images, decrypted verification bytes, per-chip bindings, logs and
captures stay under ignored `build/nomad-extension-experiment/`. Do not publish
generated vendor-derived images or reuse another module's binding.

| Evidence | File under that directory |
| --- | --- |
| Oracle probe | `oracle-probe.json` |
| Image manifest | `radio1/image.json` |
| Flash / bootloader result | `radio1/flash-result.json` |
| Callback verification / per-chip UID | `radio1/verify.json` |
| Signed vectors and 915 MHz capture | `probe2/probe.json`, `probe2/snapshot.cf32` |
| Signed vectors and 2440 MHz capture | `probe-2440/probe.json`, `probe-2440/snapshot.cf32` |
| Normal USB regression | `normal-usb-after.cf32.json` |
| Offline tests | `tests.log` |

Payload: 1828 bytes, SHA-256
`085df4ad21ca8407515199ef5f6716cbfc5afe9dcfab8ca37d4e79c68144313e`.
Custom encrypted application: 68864 bytes, SHA-256
`83f0577c4231a87b07d61f7c1eb0bbf703fe9257796c0d1d6ce4e9b86cf585cf`.

The payload was assembled with Ubuntu binutils-arc-linux-gnu 2.46-3ubuntu2 in
Ubuntu-26.04 WSL. The package was downloaded/extracted into `build/arc-prebuilt`,
without system installation. Default `tools/build_extension.py` still builds the
pinned source toolchain; `--binutils-prefix` permits an existing ARC toolchain.

To rebuild with the extracted tools, run from the repository root in WSL:

```sh
export LD_LIBRARY_PATH="$PWD/build/arc-prebuilt/sysroot/usr/lib/x86_64-linux-gnu"
python3 tools/build_extension.py --build build/nomad-extension-experiment \
  --binutils-prefix "$PWD/build/arc-prebuilt/sysroot/usr/bin/arc-linux-gnu-"
```

The installer now initializes the Nomad crystal and RF-switch profile for its
callback verification instead of using the Waveshare TCXO profile. Offline tests
check the profile selection, RAM bounds, command chunking, signed packing and
rejection of a different chip's binding.

## Repeat the RAM / RF probe

Requires this extension already installed and a successful verification report
for the selected radio. Close any other COM3 client first. Use a fresh output
directory; existing results are not overwritten.

```powershell
python host/nomad_extension_probe.py --port COM3 --radio 1 --verification build/nomad-extension-experiment/radio1/verify.json --out build/nomad-extension-experiment/repeat
```

The first attempt exposed that bulk writes to the descriptor head were rejected.
The probe now writes that head using checked masked writes, matching the existing
SDR ring setup. Failed evidence remains in `probe1/probe.json`.

## Remove the extension

Restore only radio 1's application using the checksum-pinned stock image:

```powershell
python lr1121/install.py stock --port COM3 --radio 1 --out build/nomad-extension-experiment/restore-radio1
```

This was not run after the successful experiment; radio 1 remains extended for
further testing. The ESP32 application and radio 0 do not need reflashing.

## Follow-up

The ESP32 packed-bank path is now implemented behind separate experimental
commands with per-radio binding, timeout, sequence/CRC and cancellation checks.
Native 62.5 kS/s passed continuous USB tests; native 125 kS/s passed a bounded
capture. See [packed streaming](packed-stream.md). Higher rates and FIFO service
throughput remain separate experiments.
