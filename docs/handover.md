# Handover: Nomad-SDR

Date: 2026-11-05
Workspace: `C:\Users\meawk\Desktop\Nomad-SDR`
Public repo: https://github.com/hereismeaw/Nomad-SDR
Owner: [hereismeaw](https://github.com/hereismeaw) (Kittiwut Khongkaeo)

This is the RadioMaster Nomad dual-LR1121 SDR port. Continue from here. Do not replay the Pico-only upstream as if it were this board.

## Git

| Remote | URL |
| --- | --- |
| `origin` | `https://github.com/hereismeaw/Nomad-SDR.git` (this project, public) |
| `upstream` | `https://github.com/naorunaoru/lr1121-sdr.git` (Pico tree, fetch only) |

Do not push to `upstream`. Do not commit `nomad/src/wifi.local.h`. Do not put live STA SSIDs, passwords, or LAN IPs in docs or git.

Branch: `main`. History was squashed so git authors are only hereismeaw. GitHub's Contributors widget can still show cached authors from the first push; the fix is delete-and-recreate the GitHub repo, then push `main` again.

## What is on the hardware now

- Board: RadioMaster Nomad Gemini (ESP32-PICO-D4 + two LR1121).
- Flash **main** MCU only, Windows **COM3**, Silicon Labs CP210x. Leave the ESP32-C3 backpack USB alone.
- Firmware: **nomad-0.11.0**, LR1121 transceiver **1.3 / `22030103`**, bootloader **`22df2100`**.
- **Later experiment:** radio 1 now has the FIFO1 application extension appended
  to the stock 0x0103 image. Radio 0 remains stock. Both still identify as
  `22030103`; reset clears active RAM hooks but does not remove the flash extension.
- UART: **921600** baud. 2 Mbaud hung this CP210x after boot. `info` reports `uart_baud: 921600`, `usb_compact_stream: true`.
- NVS namespace `nomadw` holds STA if the user set it over UART. Application flashing does not erase NVS. Do not switch their live STA network while testing.
- Wi-Fi AP fallback: SSID `Nomad-SDR`, password `nomadsdr1121`, IP `192.168.4.1`. TCP I/Q on **1121** (radio 0) and **1122** (radio 1).

## Live SDR

USB native (one radio per COM port). Default compact stream is **LID8 at 31.25 kS/s** so it fits 921600:

```powershell
python -m pip install -r host/requirements-live.txt
python host/nomad_rtl_tcp.py --serial COM3 --radio 0 --port 1234
```

Or `Start-Nomad-USB.cmd`. SDRangel: Remote TCP Input `127.0.0.1:1234`, **250 kHz**. SDR++: RTL-TCP, same address. The 250 kHz GUI rate is FIR-interpolated on the PC.

Wi-Fi path: `python host/nomad_rtl_tcp.py --host 192.168.4.1 --radio 0 --port 1234`

STA over USB Serial only (ASCII 32-126, quoted tokens, never echo the password, refuse while radios/TCP are active):

```powershell
python host/bridge.py --port COM3 --radio 0 wifi sta "SSID" "PASSWORD"
python host/bridge.py --port COM3 --radio 0 wifi
python host/bridge.py --port COM3 --radio 0 info
```

Bridge must keep DTR/RTS off on the Nomad CP210x. `host/bridge.py --radio` is required.

## Frequency

Synthesizer: **150-2500 MHz** on both chips.

| Band | Notes |
| --- | --- |
| 150-960 MHz | Specified RX. Nomad matching is strongest near 900 MHz. First tune: 915 MHz. |
| 1900-2200 MHz | Specified RX. |
| 2400-2500 MHz | Specified RX. Nomad 2.4 GHz antennas. First tune: 2440 MHz. Continuous 2.4 GHz still hits queue-full. |
| Gaps (1090, 1550, 2300, ...) | Synthesizer will go there. Experimental. |
| Below 150 MHz | Out of range. No FM 88-108. |

Native I/Q is 62.5 kS/s (LIQ1/LIQ8). USB live uses LID8 31.25 kS/s.

## Indicators and thermal

- WS2812 on GPIO **22**, 2 LEDs, GRB, full brightness.
- Blue = ready, green = working, yellow = buffered (queue >= 25%), red = error.
- Fan GPIO **2**: auto on at 50 C ESP32 die temp, off at 42 C. `fan auto|on|off`.
- PA APC GPIO 26 held low. Backpack EN GPIO 19 held in reset.

Pins follow ExpressLRS Nomad.json: SCK 25, MOSI 32, MISO 33, NSS 27/13, BUSY 36/39, RESET 15/21, DIO9 37/34.

## Build, test, flash, restore

```powershell
python -m pip install platformio -r host/requirements.txt -r host/requirements-live.txt
python tools/test_nomad.py
python tools/build_nomad.py
```

Flash merged image at offset 0 on COM3 from the `nomad/` directory (PlatformIO `pkg exec -d` is invalid on this PIO):

```powershell
Set-Location nomad
python -m platformio pkg exec -p tool-esptoolpy -- esptool.py --chip esp32 --port COM3 write_flash 0x0 C:\Users\meawk\Desktop\Nomad-SDR\dist\nomad\nomad-sdr-merged.bin
```

Restore ExpressLRS: `python lr1121/install.py restore-elrs` plus a full-flash backup from `build/backups/` at offset 0. ELRS radio image on disk is transceiver_drone **F30104**.

## Constraints that still apply

- UART-only credential changes. Never TCP `wifi sta`. Never print passwords.
- ASCII protocol 32-126. Quoted `nextToken` for SSID/password.
- Refuse Wi-Fi changes while streaming or radios are active.
- Compact USB streams are unlimited. LIQ1 UART is still 32 blocks.
- Do not leak `wifi.local.h`.
- English README only. No em dash `—`; use `-`.
- README Contributor is hereismeaw only. Upstream stays under Licensing, not as a project contributor.

## Semtech / Lora-net (2026-11-05)

Public org: https://github.com/orgs/Lora-net/repositories

Keep transceiver **0x0103** as the tested SDR baseline. Do not automatically flash
0x0104/0x0105 or Modem-E: SDR compatibility with their memory maps has not been
tested. 0x0104 adds low latency APIs and security fixes; 0x0105 fixes
CVE-2026-6232. Modem-E does expose direct radio access in suspended mode, so do
not claim it removes all radio/memory access. GNSS, Wi-Fi geolocation, RTToF and
BLE beacon compatibility are LR1110/LR1120 features, not LR1121.

Useful leftover APIs: LoRa/GFSK packet RX, CAD, `GetRssiInst` sweep,
RxBoosted / LF0 input topology, and radio die temperature/supply diagnostics.
Do not infer BPSK or LR-FHSS RX support merely from packet-type enums.
Highest-value Nomad experiments: RSSI sweep, LoRa/GFSK packet monitor, or port
FIFO1 (ARC extension, Pico LIP2/LIP3) onto the ESP32 SPI HAL while still on
0x0103. The shared ESP32 SPI runs at 16 MHz and limits high-rate acquisition.
See [source review and implementation priorities](lr1121-research.md), including
pinned upstream revisions and the limits of each proposal.

## Open work

- ARC packed streaming on radio 1 now passes via ESP32/USB. See
  [packed streaming](packed-stream.md) for commands, results and limits.
  Remaining: sustained packed TCP, dual-radio, and higher-rate/FIFO service tests.
- USB rtl_tcp hardware smoke now passes. A full SDRangel GUI session on `--serial COM3` has not been tested in this continuation.
- Wi-Fi continuous 2.4 GHz and dual-radio streaming previously hit queue-full; not retested in this continuation. USB radio 1 at 2440 MHz passed an 8-second capture, which does not prove indefinite operation.
- No RF reference tone, so Nomad matching/sensitivity is unproven outside 900 / 2.4 GHz antennas.
- Pico LIP2/LIP3, TX player, native SDR++ module: not on ESP32 yet.
- SDR++ GUI was not run on this PC.

## Continuation results (2026-11-05)

The earlier firmware 0.9.2 was built, packaged and flashed to the main ESP32
application at `0x10000` on COM3 with esptool hash verification. Current firmware
is 0.10.0, described below.
No LR1121 firmware or Wi-Fi credentials were changed. This continuation is committed on `main`.

USB setup initially failed with truncated ASCII ring-write commands. The default
256-byte UART RX buffer was insufficient at 921600 baud. RX now holds a complete
`BRIDGE_LINE_SIZE` command. A 4096-byte UART TX ring also removes gaps caused by
blocking each frame on the hardware FIFO. Without the TX change an 8-second LID8
capture stopped after about one second with queue-full; with it all checks below pass.

Version 0.9.2 also calls indicator updates every 20 ms inside serial stream(),
which otherwise blocks Arduino loop() for the entire capture. This keeps fan
temperature sampling (every 250 ms) and RGB radio status active during indefinite
USB acquisition. TCP continues using the ordinary loop() update path.

- Radio 0, 915 MHz: 8 seconds, 4000 banks, 250000 samples at 31250 S/s,
  flags 0, lost samples 0, maximum queue 3.
  Evidence: `build/continuation-usb-radio0-buffered.cf32.json`.
- Radio 1, 915 MHz and 2440 MHz separately: same sample counts, flags 0,
  lost samples 0, maximum queue 3.
  Evidence: `build/continuation-usb-radio1-buffered.cf32.json` and
  `build/continuation-usb-radio1-2440.cf32.json`.
- USB -> rtl_tcp loopback client, 60 seconds, 915 -> 245 MHz retune:
  28610 received banks, 28344000 forwarded bytes, zero underruns, no errors.
  Both jobs cancelled cleanly with flag 4 and lost samples 0; maximum queue 4.
  Maximum input frame gap 24.6 ms. Maximum output gap 1.75 s includes retune/setup.
  Evidence: `build/continuation-live-usb-radio0.json`.
- Repeated the same 60-second test after the 0.9.2 indicator-loop fix:
  28759 banks, 28512000 bytes, zero underruns, no errors, both cancellations
  clean (flag 4, no lost samples). Maximum input gap 9.83 ms and output gap
  1.52 s including retune/setup. Evidence: `build/continuation-live-usb-v092.json`.
- Fan on/off/auto and individual LED0/LED1 colors returned success over UART;
  both controls restored to auto. This verifies commands/status, not physical
  fan rotation or visible colors. Evidence: `build/continuation-indicators.json`.
- Offline checks: 67 host tests, 15 LR1121 tests and three C suites pass.
  Added LID8 alternating dimensions, sample indices, CRC, terminal decoding,
  interpolation across odd bank boundaries, and USB decimation regression coverage.

`host/nomad_rx.py --decimate` now implies compact before the USB size guard.
USB recording documentation uses LID8 instead of LIQ8, whose 147500 B/s exceeds
921600-baud UART capacity. Default live rate is 31250 S/s for both transports.

Re-run the receive-only test with:

```powershell
python tools/smoke_nomad_live.py --serial COM3 --radio 0 --seconds 60
```

This creates a temporary local TCP server, retunes halfway and writes
`build/live-smoke.json`. It does not modify SDRangel presets. The old Wi-Fi
proxy processes on ports 1234/1235 were stopped after checking their exact
command lines. No replacement proxy was left running; `Start-Nomad-USB.cmd`
can now use port 1234. STA was disconnected during the final check; its saved
configuration was preserved.

## Packed streaming continuation (2026-11-05)

Firmware **0.10.0** is built and flashed at `0x10000` with hash verification.
No LR1121 application/bootloader updates were needed in this continuation.
Radio 1 retains the previously verified extension; radio 0 remains stock.

- `streampd RATE BLOCKS UID` and `streamp8 RATE BLOCKS UID` opt into ARC IQ8
  acquisition. Existing commands retain the raw path. Firmware checks the
  physical UID/version, extension state and complete ring before enabling ADC.
- `host/nomad_rx.py`, `host/nomad_rtl_tcp.py` and the hardware smoke tool accept
  `--packed-verification build/nomad-extension-experiment/radio1/verify.json`.
  Select radio 1 explicitly. Retunes reconfigure and recheck the callback.
- Two 60-second USB rtl_tcp tests passed: 915 -> 245 MHz and 2440 -> 2470 MHz.
  Both used ARC acquisition, had zero underruns/lost samples and clean flag-4
  cancellations. Maximum firmware queue depth was 2. Evidence:
  `build/packed-stream-live-usb.json`, `build/packed-stream-live-2g4.json`.
- Native 125 kS/s passed a 100-bank / 0.1-second capture, output 6250 samples
  at 62500 S/s after /2. UART cannot sustain this output; host and firmware
  limit above-capacity packed USB modes to 128 native banks. Indefinite USB
  packed live uses native 62500, LID8 output 31250 S/s.
- Malformed/wrong UID and above-capacity indefinite USB commands were rejected
  while ADC gate remained off (`build/packed-stream-admission.json`).
- Final image passed another 15-second packed retune smoke. Normal radio 1
  passed 8 seconds and stock radio 0 passed 2 seconds with no loss.
- Offline validation: 73 host tests, 17 LR1121 tests and three C suites passed.
  Added ARC bank endianness/sequence-wrap/scale and signed expansion tests.

No proxy was left running. Start packed USB with:

```powershell
python host/nomad_rtl_tcp.py --serial COM3 --radio 1 --port 1234 --packed-verification build/nomad-extension-experiment/radio1/verify.json
```

SDRangel/SDR++ still connects to localhost:1234 at 250000 S/s. This is PC
interpolation, not additional RF bandwidth. Actual GUI and sustained TCP/dual
packed modes remain untested. See [packed-stream.md](packed-stream.md).

## Docs

[USB native](usb-native.md) · [live SDR](live-sdr.md) · [Nomad port](nomad.md) · [LIQ8](LIQ8.md) · [LR1121 install](lr1121-install.md) · [extension experiment](nomad-extension-experiment.md) · [packed streaming](packed-stream.md)

## Control API continuation (2026-11-05)

Firmware **0.11.0** adds native `capabilities` and `stream status` without SPI
access. Stream telemetry includes last accepted mode/rate, queue estimate,
produced/sent frames, flags, complete-frame bytes and average throughput.
Mode snapshots are kept separately from parser options so later info/read RPCs
do not change the last stream's reported format. Elapsed time is 64-bit here;
the existing binary wire timestamps retain their previous format.

All nine requested API groups are implemented in `host/nomad_control.py` and
served by `host/nomad_api.py` at localhost:8094 under `/api/v1`. Start with
`Start-Nomad-API.cmd` or `python host/nomad_api.py --serial COM3`.
See [control-api.md](control-api.md) for the complete routes and examples.

- RX/packet configuration supports LoRa and GFSK. CAD is receive-only.
- Persistent connections retain configuration; a shared lock makes radio
  selection + requests atomic for two jobs on the same USB UART.
- Sweep/packet jobs support cancellation, bounded results, CSV, status/error
  reporting and dual plans. Wrong-kind stop or reconfigure during a job is 409.
- Gain exposes AGC/manual register step, RxBoosted and LF0 topology with
  register readbacks. The saved post-reset AGC control is restored on AGC enable.
- Diagnostics reads both LR1121 temperature/supply values with nominal scaling.
  It resumes a manually running receiver, and refuses during a background job.
- Packet buffer is frozen for copying; explicit LoRa headers determine CRC
  presence. No-CRC packets report crc_ok null. Hardware drop counts are unknown,
  distinct from host-buffer eviction counters.
- Receive-only HTTP hardware checks passed on COM3, including dual sweep+packet,
  all three LNA topologies and diagnostics resume. Evidence:
  `build/api-hardware-final.json`. Positive RF packet decoding and detection
  probability still require a reference transmitter; packet worker/parser have
  synthetic positive-path tests.
- Offline validation: 87 host tests, 17 LR1121 tests and three C suites passed.
  Core new tests cover invalid configs without I/O, serial selection concurrency,
  job cancellation/failure, packet CRC/SNR, dual rollback and HTTP errors.
- Final firmware passed a 15-second packed retune smoke with zero underruns.
  Telemetry matched its terminal counters and complete-frame bytes, reporting
  84894 B/s average. An intervening info RPC preserved the last stream format.
  Evidence: `build/api-packed-final.json`, `build/api-stream-telemetry.json`.
  The final HTTP recheck passed 43 requests (`build/api-hardware-final.json`).

The API server owns COM3 while running. Close it before starting USB I/Q proxy
or recorder. This API dual mode is packet/sweep work sharing, not dual USB I/Q.
No server was left running after verification. No LR1121 flash/bootloader or
saved Wi-Fi changes were made in this continuation; fan and RGB remain auto.
