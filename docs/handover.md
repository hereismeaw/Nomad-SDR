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
- Firmware: **nomad-0.9.0**, stock LR1121 transceiver **1.3 / `22030103`**, bootloader **`22df2100`**.
- UART: **921600** baud. 2 Mbaud hung this CP210x after boot. `info` reports `uart_baud: 921600`, `usb_compact_stream: true`.
- NVS namespace `nomadw` holds STA if the user set it over UART. A 0.9.0 flash does not erase NVS. Do not switch their live STA network while testing.
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

Stay on transceiver **0x0103**. Do not flash **0x0105** (CVE-2026-6232 SPI OOB write patch) or **Modem-E**; both can kill the I/Q / ARC installer path. GNSS, Wi-Fi geolocation, RTToF, BLE beaconing are LR1110/LR1120 only. LR1121 does not have them.

Useful leftover APIs: LoRa/GFSK/BPSK/LR-FHSS packet RX, CAD, `GetRssiInst` sweep, RxBoosted / LNA mode, 2.4 GHz LoRa BW 200/400/800 kHz. Highest-value Nomad experiments: dual-chip ELRS/LoRa sniffer, or port FIFO1 (ARC extension, Pico LIP2/LIP3) onto the ESP32 SPI HAL while still on 0x0103. ESP32 SPI is 16 MHz; that is the 250/500 kS/s bottleneck.

## Open work

- USB native was prepared and `info` verified. A full SDRangel session on `--serial COM3` was not smoked in the last turn.
- Continuous 2.4 GHz and dual-radio streaming still queue-full.
- No RF reference tone, so Nomad matching/sensitivity is unproven outside 900 / 2.4 GHz antennas.
- Pico LIP2/LIP3, TX player, native SDR++ module: not on ESP32 yet.
- SDR++ GUI was not run on this PC.

## Docs

[USB native](usb-native.md) · [live SDR](live-sdr.md) · [Nomad port](nomad.md) · [LIQ8](LIQ8.md) · [LR1121 install](lr1121-install.md)
