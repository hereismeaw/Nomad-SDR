# USB native mode

Nomad firmware 0.9.2 streams compact I/Q over the main ESP32 CP210x UART at
**921 600 baud**. This is the USB native path for a single radio. The backpack
USB port is not used.

LID8 at 31.25 kS/s fits this UART. LIQ1 still uses a 32-block smoke capture.

## Live SDRangel / SDR++

```powershell
python host/nomad_rtl_tcp.py --serial COM3 --radio 0 --port 1234
```

Or double-click `Start-Nomad-USB.cmd`. Leave that window open, then in SDRangel
choose Remote TCP Input (or SDR++ RTL-TCP) at `127.0.0.1:1234` and **250 kHz**.

Radio 1 uses `--radio 1 --port 1235`. One USB UART owns one radio at a time.

## Recorder

```powershell
python host/nomad_rx.py --port COM3 --radio 0 --decimate --frequency 915000000 --seconds 8 --output usb-radio0.cf32
```

## Serial control at the same baud

`host/bridge.py` opens Nomad at 921600 baud when `--radio` is set:

```powershell
python host/bridge.py --port COM3 --radio 0 info
python host/bridge.py --port COM3 --radio 0 wifi
python host/bridge.py --port COM3 --radio 0 wifi sta "SSID" "PASSWORD"
```

Firmware 0.9.2 reports `uart_baud: 921600` and `usb_compact_stream: true`.
Open a 0.8.0 board at 115200 until it is reflashed. Default live USB rate is LID8 31.25 kS/s.

Use `--decimate` for sustained USB recording. `--compact` alone selects LIQ8
at 62.5 kS/s, which exceeds the 921600-baud UART capacity. Firmware 0.9.1
adds full-command RX buffering and a 4096-byte TX ring to prevent truncated
setup commands and gaps between frame writes.
Firmware 0.9.2 also services fan temperature control and RGB status every 20 ms
inside the USB stream loop; temperature sampling retains its 250 ms interval.

For a receive-only rtl_tcp hardware check, including a frequency change:

```powershell
python tools/smoke_nomad_live.py --serial COM3 --radio 0 --seconds 60
```

This uses a temporary local TCP port and writes `build/live-smoke.json`.
It checks the protocol and sample flow; it does not test a GUI or RF sensitivity.
