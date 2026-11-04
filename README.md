# Nomad-SDR

**Two Semtech LR1121 radios. One RadioMaster Nomad. A pocket wideband receiver that talks to SDRangel and SDR++.**

![Nomad-SDR live in SDRangel](docs/images/nomad-sdrangel.jpg)

Firmware on the Nomad's main ESP32 turns the stock dual-LR1121 Gemini board into an I/Q source. Tune **150-2500 MHz**, watch the waterfall, and keep ExpressLRS a restore away.

## Live in one command

USB native (CP210x on the **main** MCU, COM3 on Windows):

```powershell
python -m pip install -r host/requirements-live.txt
python host/nomad_rtl_tcp.py --serial COM3 --radio 0 --port 1234
```

Or double-click `Start-Nomad-USB.cmd`. In SDRangel pick **Remote TCP Input** (SDR++: **RTL-TCP**) at `127.0.0.1:1234` and **250 kHz**.

Wi-Fi AP is `Nomad-SDR` / `nomadsdr1121` at `192.168.4.1`. STA credentials can be written over USB:

```powershell
python host/bridge.py --port COM3 --radio 0 wifi sta "SSID" "PASSWORD"
python host/nomad_rtl_tcp.py --host 192.168.4.1 --radio 0 --port 1234
```

## What you get

| | |
| --- | --- |
| Radios | Dual LR1121, ExpressLRS Nomad pin map, stock transceiver 1.3 |
| Live path | LIQ8 / LID8 to local rtl_tcp for SDRangel and SDR++ |
| USB native | 921600 baud LID8 I/Q on the main UART, one radio at a time |
| Wi-Fi | TCP 1121 / 1122, UART `wifi sta` stored in NVS |
| Tune | 150-2500 MHz synthesizer; matching is best on Nomad's 900 / 2.4 GHz antennas |
| Status | Full-brightness RGB: blue ready, green working, yellow buffered, red error |
| Thermal | Fan on at 50 °C die temperature, off at 42 °C |

## Frequency

Both radios tune **150-2500 MHz**. That is the LR1121 synthesizer span, not a promise of even sensitivity.

| Band | Support |
| --- | --- |
| 150-960 MHz | Specified RX. Nomad matching and antennas are strongest near 900 MHz (915 MHz is the usual first tune). |
| 1900-2200 MHz | Specified RX. |
| 2400-2500 MHz | Specified RX. Nomad 2.4 GHz antennas (2440 MHz is the usual first tune). |
| Gaps in 960-1900 and 2200-2400 MHz | Synthesizer will go there (1090, 1550, 2300 MHz were tried). Treat those as experiments. |
| Below 150 MHz | Out of range. FM broadcast 88-108 MHz is not supported. |
| Above 2500 MHz | Out of range. |

Native I/Q is 62.5 kS/s (USB LID8 31.25 kS/s). The 250 kHz rate in SDRangel is interpolated on the PC.

Guides: [USB native](docs/usb-native.md) · [live SDR](docs/live-sdr.md) · [Nomad port](docs/nomad.md) · [LIQ8](docs/LIQ8.md)

## Build and flash

```powershell
python -m pip install platformio -r host/requirements.txt -r host/requirements-live.txt
python tools/test_nomad.py
python tools/build_nomad.py
```

Flash the merged image at offset `0x0` on the **main** ESP32-PICO-D4 (CP210x). Leave the backpack USB alone.

```powershell
python -m platformio pkg exec -p tool-esptoolpy -- esptool.py --chip esp32 --port COM3 write_flash 0x0 dist/nomad/nomad-sdr-merged.bin
```

Run that from the `nomad/` directory, or pass the absolute path to `nomad-sdr-merged.bin`.

Restore ExpressLRS with `python lr1121/install.py restore-elrs` plus a full-flash backup from `build/backups/`.

## Honest limits

Continuous 2.4 GHz and dual-radio streaming are still rough. Sensitivity outside Nomad's matched bands is unproven. The Pico LIP2/LIP3 250/500 kS/s path, TX, and native SDR++ module stay on the upstream RP2040 tree.

## Layout

- `nomad/` - ESP32 firmware (PlatformIO, MIT)
- `host/` - UART/TCP bridge, recorder, rtl_tcp adapter
- `pico/` - original RP2040 firmware from [lr1121-sdr](https://github.com/naorunaoru/lr1121-sdr)
- `sdrpp/` - GPL-3.0 SDR++ source module for the Pico
- `docs/` - hardware notes, live setup, measurements

## Contributor

[hereismeaw](https://github.com/hereismeaw)

## Licensing

This tree started from [naorunaoru/lr1121-sdr](https://github.com/naorunaoru/lr1121-sdr). Pin map from [ExpressLRS Nomad](https://github.com/ExpressLRS/targets). LR1121 research lineage includes [radioegor146/lr-semtech-research](https://github.com/radioegor146/lr-semtech-research).

Independent firmware, host tools and docs: [MIT](LICENSE).
`sdrpp/` and Nomad receiver helpers derived from it: [GPLv3](sdrpp/LICENSE).
See [license scope](docs/licensing.md) and [third-party notices](THIRD_PARTY_NOTICES.md).
Semtech LR1121 images keep their vendor license. Do not commit `nomad/src/wifi.local.h`.
