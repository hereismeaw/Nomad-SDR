# Experimental ARC packed streaming on Nomad

Firmware **nomad-0.10.0** adds an opt-in acquisition path that reads I/Q already
packed to signed 8-bit components by the LR1121 ARC extension. Ordinary commands
keep using their previous raw acquisition path. Only radio 1 currently has the
required extension installed; see [installation evidence](nomad-extension-experiment.md).

## Live USB with SDRangel / SDR++

From PowerShell in the repository root, with other COM3 clients closed:

```powershell
python host/nomad_rtl_tcp.py --serial COM3 --radio 1 --port 1234 --packed-verification build/nomad-extension-experiment/radio1/verify.json
```

Keep the proxy running. Connect SDRangel Remote TCP Input or SDR++ RTL-TCP to
`127.0.0.1:1234` with sample rate **250000**, IQ **8 bits**. The GUI rate is PC
interpolation. Actual acquisition is **62500 S/s**, FIR-decimated on ESP32 to
**31250 S/s** for USB transport. Received RF bandwidth does not become 250 kHz.

Without `--packed-verification`, the proxy uses the normal acquisition path.
The verification file is specific to the physical chip and is not bundled in git.

## Recording and verification

```powershell
python host/nomad_rx.py --port COM3 --radio 1 --frequency 915000000 --seconds 8 --decimate --packed-verification build/nomad-extension-experiment/radio1/verify.json --output build/packed-recording.cf32
python tools/smoke_nomad_live.py --serial COM3 --radio 1 --packed-verification build/nomad-extension-experiment/radio1/verify.json --seconds 60 --report build/packed-live-check.json
```

Recording metadata and live job reports identify `acquisition: arc8`.
LID8/LIQ8 decoding, payload/header CRC and frame/sample sequence checks remain
the same. ARC packing truncates/saturates components; this path is not bit-identical
to the original raw signed-23 acquisition followed by PC or ESP32 processing.

## Device commands and checks

| Command | Output |
| --- | --- |
| `ID streampd RATE BLOCKS UID` | ARC IQ8 expanded into the existing ESP32 FIR /2, sent as LID8 |
| `ID streamp8 RATE BLOCKS UID` | ARC IQ8 forwarded as LIQ8 without another quantizer |

`RATE` is native 62500 or 125000. `UID` is the 16-hex-character UID from the
successful extension verification. `BLOCKS` counts native 125-sample banks;
zero requests indefinite operation. Host setup checks the binding and executes
the extension callback self-test before preparing the 16-bank ring.

Before opening the ADC gate, ESP32 checks the actual radio version and UID,
markers, callback entry, packer state, zero initial producer counters/ready flags,
native decimator, disabled gate, DMA pointer and all 16 descriptors. During
acquisition it checks packed-bank markers/sequence/scale and DMA ownership,
then rearms the descriptor and clears its ready flag after copying the payload.
These are compatibility guards, not cryptographic attestation.

ETX cancels the job, drains queued frames and sends a terminal frame. Flag 4
means deliberate cancellation; queue-full, starvation or format errors remain
failures. The packer is disabled when acquisition finishes. A fresh configure
resets the radio and rechecks the extension on every retune.

## Transport limits

USB UART is 921600 baud. Sustained USB live requires `streampd 62500`, yielding
85000 B/s including frame headers. Undecimated IQ8, or native 125 kS/s with only
/2 decimation, exceeds this UART capacity. Both host and firmware restrict those
USB experimental captures to **128 native banks**. They do not silently drop or
pad samples to make them fit.

Example of the tested short native-125 kS/s capture:

```powershell
python host/nomad_rx.py --port COM3 --radio 1 --rate 125000 --seconds 0.1 --decimate --packed-verification build/nomad-extension-experiment/radio1/verify.json --output build/packed-125k.cf32
```

TCP commands use the same acquisition path without this UART-specific cap.
Sustained packed TCP, dual-radio acquisition and native 250/500 kS/s have not
been hardware-tested in this work. The host live proxy still uses native 62.5 kS/s.

## Hardware results: 2026-11-05

| Check | Observed result | Evidence under `build/` |
| --- | --- | --- |
| Packed USB, 2 seconds at 915 MHz | 1000 banks, 62500 output samples, flags/loss 0 | `packed-stream-first.cf32.json` |
| Live USB, 60 seconds, 915 -> 245 MHz | 28089 banks, 0 underruns, 0 loss, both ETX cancellations clean, max queue 2 | `packed-stream-live-usb.json` |
| Live USB, 60 seconds, 2440 -> 2470 MHz | No errors/underruns/loss; both jobs report ARC acquisition | `packed-stream-live-2g4.json` |
| Native 125 kS/s, 0.1 seconds | 100 banks, 6250 output samples at 62.5 kS/s after /2; flags/loss 0 | `packed-stream-125k.cf32.json` |
| Rejected malformed/mismatched UID and oversized USB mode | ADC gate remained disabled | `packed-stream-admission.json` |
| Normal USB after packed tests, 8 seconds | 250000 output samples, flags/loss 0 | `packed-stream-normal-after.cf32.json` |

The first live test had a maximum input gap of 8.71 ms. Its maximum output gap
of 2.30 seconds includes retune/setup and extension verification. No artificial
samples are generated during that gap. The GUI integration is checked through
the rtl_tcp protocol client; an SDRangel/SDR++ GUI was not run in this work.

The bus reads 256 bytes for a packed bank, compared with 1000 raw sample bytes
before packing. Additional status, pointer and ownership transactions remain.
This measurement does not establish a fourfold overall speed increase or RF
sensitivity. No calibrated reference tone was used.
