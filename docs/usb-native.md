# USB native mode

Nomad firmware 0.9.0 streams compact I/Q over the main ESP32 CP210x UART at
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
python host/nomad_rx.py --port COM3 --radio 0 --compact --frequency 915000000 --seconds 8 --output usb-radio0.cf32
```

## Serial control at the same baud

`host/bridge.py` opens Nomad at 921600 baud when `--radio` is set:

```powershell
python host/bridge.py --port COM3 --radio 0 info
python host/bridge.py --port COM3 --radio 0 wifi
python host/bridge.py --port COM3 --radio 0 wifi sta "SSID" "PASSWORD"
```

Firmware 0.9.0 reports `uart_baud: 921600` and `usb_compact_stream: true`.
Open a 0.8.0 board at 115200 until it is reflashed. Default live USB rate is LID8 31.25 kS/s.
