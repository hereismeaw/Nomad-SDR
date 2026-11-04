# Handover: RadioMaster Nomad SDR

วันที่ 2026-11-04 เซสชัน Codex พอร์ต [lr1121-sdr](https://github.com/naorunaoru/lr1121-sdr) ลง RadioMaster Nomad (LR1121 ×2) แล้วขอให้เขียน handover และเพิ่มพัดลมกับ RGB LED

สาขา: `main` จาก upstream Pico TX ISR พร้อมเฟิร์มแวร์ Nomad

## เป้าหมายล่าสุด

1. ให้เซสชันถัดไปทำต่อได้โดยไม่ต้องไล่ประวัติ
2. รองรับพัดลม GPIO2 และ WS2812 GPIO22 ตาม ExpressLRS Nomad target

## สิ่งที่ทำแล้ว (ตรวจใน repo)

- เฟิร์มแวร์ Arduino/PlatformIO ใน `nomad/` บน ESP32-PICO-D4 ของ Nomad
- Pin mapping ตาม [ExpressLRS Nomad.json](https://github.com/ExpressLRS/targets/blob/master/TX/Radiomaster%20Nomad.json)
- Wi-Fi STA ตั้งผ่าน UART (`wifi sta`) หรือ `nomad/src/wifi.local.h` ที่ gitignore
- TCP 1121 / 1122, UART COM3 CP210x, สำรองแฟลชใน `build/backups/`
- LR1121 ทั้งคู่เป็น stock transceiver 1.3 `22030103` bootloader `22df2100`
- Live path: LIQ8 / LID8 + `host/nomad_rtl_tcp.py` สำหรับ SDRangel Remote TCP Input และ SDR++ RTL-TCP
- จูน synthesizer 150–2500 MHz; ตรวจสั้น 26/26 ความถี่บนฮาร์ดแวร์
- เฟิร์มแวร์ **0.7.0** ใช้พัดลมตามอุณหภูมิได ESP32 และ RGB ความสว่างเต็ม: น้ำเงินพร้อมใช้ / เขียวกำลังทำงาน / เหลือง buffered / แดง error

คู่มือใช้งาน: [docs/nomad.md](nomad.md), [docs/live-sdr.md](live-sdr.md), [docs/LIQ8.md](LIQ8.md)

## ฮาร์ดแวร์

| สัญญาณ | GPIO |
| --- | --- |
| SCK / MOSI / MISO | 25 / 32 / 33 |
| NSS 0 / 1 | 27 / 13 |
| BUSY 0 / 1 | 36 / 39 |
| RESET 0 / 1 | 15 / 21 |
| DIO9 0 / 1 | 37 / 34 |
| PA APC | 26 (ดึงต่ำ) |
| Fan enable | 2 (ปริยายเปิด) |
| Backpack EN | 19 (ค้างรีเซ็ต) |
| WS2812 RGB | 22, 2 ดวง, ลำดับ GRB |

อย่าใช้ USB ของ ESP32-C3 backpack แฟลช image นี้ เครื่องที่ทดสอบเข้า main MCU ผ่าน COM3

กู้ ELRS: restore LR ด้วย `python lr1121/install.py restore-elrs` แล้วเขียน full backup ที่ offset 0

## คำสั่งที่ควรใช้ต่อ

```powershell
python -m pip install platformio -r host/requirements.txt -r host/requirements-live.txt
python tools/test_nomad.py
python tools/build_nomad.py
python host/bridge.py --port COM3 --radio 0 info
python host/bridge.py --port COM3 --radio 0 wifi
python host/bridge.py --port COM3 --radio 0 fan
python host/bridge.py --port COM3 --radio 0 led
python host/nomad_rtl_tcp.py --serial COM3 --radio 0 --port 1234
```

หรือดับเบิลคลิก `Start-Nomad-SDR.cmd` แล้วเปิด SDRangel/SDR++ ที่ `127.0.0.1:1234` sample rate **250 kHz**

พัดลม: `fan auto` (ปริยาย, เปิด ≥50 °C ปิด ≤42 °C), `fan on`, `fan off`  
LED ความสว่างเต็ม: น้ำเงินพร้อมใช้, เขียวกำลังรับ, เหลืองคิว ≥25%, แดง error

## งานที่ยังเปิด

- Capture ต่อเนื่อง 2440/2470 MHz ยังเจอ queue-full เป็นครั้งคราว ไม่รับรอง 2.4 GHz ยาวๆ
- ยังไม่รับรองสองช่องพร้อมกันและความต่อเนื่องของ sample clock ข้ามชิป
- ยังไม่มี RF reference tone จึงยังไม่รับรอง sensitivity/bandwidth ของวงจร Nomad
- SDR++ GUI บน PC นี้ยังไม่ได้รัน มีแค่ความเข้ากันได้ของ source/rtl_tcp
- Pico LIP2/LIP3, TX, reset guard, โมดูล SDR++ เฉพาะทาง ยังไม่พอร์ต
- ไฟล์ Nomad ส่วนใหญ่ยัง untracked/modified ยังไม่ได้ commit

## จุดที่หยุดและงานถัดไปที่ปลอดภัย

เซสชันนี้เพิ่ม indicators แล้ว ขั้นถัดไปที่ปลอดภัยคือบิลด์ 0.6.0, แฟลช COM3, แล้วตรวจ `info` / `fan` / `led` / `wifi` บนเครื่องจริง จากนั้นค่อยไล่ queue-full ที่ 2.4 GHz ถ้าต้องการความต่อเนื่อง
