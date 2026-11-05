# Nomad-SDR

**วิทยุ LR1121 สองตัวบน RadioMaster Nomad — รับกว้าง 150–2500 MHz ดู waterfall ใน SDRangel / SDR++ และสั่งงานผ่าน JSON API**

![Nomad-SDR live in SDRangel](docs/images/nomad-sdrangel.jpg)

เฟิร์มแวร์บน ESP32 ตัวหลักของ Nomad แปลงบอร์ด Gemini สองชิปให้เป็นเครื่องรับ I/Q
จูนความถี่จากโปรแกรม SDR ได้ และคืน ExpressLRS ได้จาก backup

| | |
| --- | --- |
| ชิป | LR1121 สองตัว (ExpressLRS Nomad), transceiver 1.3 |
| USB | สาย **ตัวหลัก** (CP210x) ความเร็ว 921600 baud, รับทีละชิป |
| Wi-Fi | AP `Nomad-SDR` / `nomadsdr1121` ที่ `192.168.4.1` หรือต่อเราเตอร์แบบ STA |
| Waterfall | LID8 → `nomad_rtl_tcp.py` → SDRangel Remote TCP Input / SDR++ RTL-TCP |
| Control API | `http://127.0.0.1:8094/api/v1` สำหรับ sweep, packet, CAD, gain, diagnostics |
| ไฟสถานะ | น้ำเงินพร้อมใช้ · เขียวกำลังรับ · เหลืองคิวหนา · แดงผิดพลาด |
| พัดลม | เปิดที่ได ESP32 ≥ 50 °C ปิดที่ ≤ 42 °C |

---

## สารบัญ

1. [เลือกโหมดการใช้งาน](#เลือกโหมดการใช้งาน)
2. [ของที่ต้องมี](#ของที่ต้องมี)
3. [ติดตั้งครั้งแรก](#ติดตั้งครั้งแรก)
4. [ดู waterfall ผ่าน USB](#ดู-waterfall-ผ่าน-usb)
5. [ใช้ผ่าน Wi-Fi](#ใช้ผ่าน-wi-fi)
6. [Control API (สแกน / จับแพ็กเก็ต)](#control-api-สแกน--จับแพ็กเก็ต)
7. [ความถี่และเสาอากาศ](#ความถี่และเสาอากาศ)
8. [แฟลชเฟิร์มแวร์และคืน ExpressLRS](#แฟลชเฟิร์มแวร์และคืน-expresslrs)
9. [ปัญหาที่พบบ่อย](#ปัญหาที่พบบ่อย)
10. [ข้อจำกัด](#ข้อจำกัด)

รายละเอียดเพิ่ม: [USB native](docs/usb-native.md) · [live SDR](docs/live-sdr.md) · [control API](docs/control-api.md) · [Nomad](docs/nomad.md)

---

## เลือกโหมดการใช้งาน

ใช้ทีละโหมด เพราะ **COM3 เปิดได้ทีละโปรแกรม**

| อยากทำอะไร | เปิดอะไร | อย่าเปิดพร้อมกัน |
| --- | --- | --- |
| ดู waterfall / ฟังเสียง | `Start-Nomad-USB.cmd` แล้วเปิด SDRangel หรือ SDR++ | API server, recorder |
| PC ไม่มี Wi-Fi หรืออยากเสถียรสุด | USB ตามแถวบน | — |
| PC อยู่คนละเครื่อง / ใช้สาย LAN | ต่อ Nomad Wi-Fi แล้ว `Start-Nomad-SDR.cmd` | USB proxy บนพอร์ตเดียวกัน |
| สแกน RSSI, จับ LoRa/GFSK, อ่านอุณหภูมิชิป | `Start-Nomad-API.cmd` | USB waterfall |
| บันทึกไฟล์ I/Q สั้นๆ | `host/nomad_rx.py` | USB proxy และ API |

ชิป **0** เหมาะย่าน 900 MHz (เริ่มที่ 915 MHz)
ชิป **1** เหมาะย่าน 2.4 GHz (เริ่มที่ 2440 MHz)
USB ส่ง I/Q ได้ทีละชิป Wi-Fi แยกพอร์ต 1121 / 1122 แต่สตรีมสองชิปพร้อมกันยังไม่รับรอง

---

## ของที่ต้องมี

- RadioMaster Nomad (Gemini, สอง LR1121)
- Windows, Python 3, สาย USB เข้าพอร์ต **ตัวหลัก** (Silicon Labs CP210x)
- **อย่าใช้พอร์ต backpack** (ESP32-C3) สำหรับงานนี้
- SDRangel หรือ SDR++ ถ้าจะดู waterfall
- เสาอากาศ 900 MHz และ/หรือ 2.4 GHz ที่มากับโมดูล

ดูหมายเลข COM ใน Device Manager → Ports (COM & LPT) → Silicon Labs
คู่มือนี้ใช้ **COM3** ตามเครื่องที่ทดสอบ ถ้าเครื่องคุณเป็น COM อื่น ให้แก้ในคำสั่งหรือไฟล์ `.cmd`

---

## ติดตั้งครั้งแรก

เปิด PowerShell ที่โฟลเดอร์ repo นี้:

```powershell
python -m pip install -r host/requirements-live.txt
```

ถ้ายังไม่ได้แฟลชเฟิร์มแวร์ Nomad-SDR ให้ทำตาม [แฟลชเฟิร์มแวร์](#แฟลชเฟิร์มแวร์และคืน-expresslrs) ก่อน
เฟิร์มแวร์ที่ใช้เส้นทางนี้คือ **nomad-0.11.0**

ตรวจว่าบอร์ดตอบ:

```powershell
python host/bridge.py --port COM3 --radio 0 info
```

คำตอบที่ต้องการมี `"firmware":"nomad-0.11.0"` และ `"board":"radiomaster-nomad"`
ถ้าเปิดพอร์ตไม่ได้ ให้ปิด SDRangel, API, และหน้าต่าง Python อื่นที่ถือ COM3 อยู่

---

## ดู waterfall ผ่าน USB

นี่คือทางหลักที่เสถียรที่สุดบนเครื่องที่ทดสอบ

### 1. เปิดตัวเชื่อมบน PC

ดับเบิลคลิก `Start-Nomad-USB.cmd` หรือรัน:

```powershell
python host/nomad_rtl_tcp.py --serial COM3 --radio 0 --port 1234
```

ปล่อยหน้าต่างนี้เปิดไว้ จะได้บริการที่ `127.0.0.1:1234`
ตัวเชื่อมไปคุยกับ Nomad เมื่อโปรแกรม SDR กด Start เท่านั้น
กด Ctrl+C ในหน้าต่างนี้เมื่อเลิกใช้

ชิป 1 ใช้ `--radio 1 --port 1235`

### 2. SDRangel

1. เพิ่ม Rx device เลือก **Remote TCP Input**
2. Server `127.0.0.1` พอร์ต `1234`
3. Protocol เลือก **SDRangel** (ตัวรับจะใช้ RTL0 ให้เอง)
4. Device / Channel sample rate **250000**, decimation 1, sample bits **8**
5. เปิด **Override remote settings**
6. ความถี่กลาง **915000000** Hz แล้ว Start
7. เพิ่มช่อง **NFM Demodulator** หรือ demodulator ที่ต้องการ

### 3. SDR++

1. Source เลือก **RTL-TCP**
2. Host `127.0.0.1` พอร์ต `1234`
3. Sample rate **250 kHz** ก่อนกด Play (ค่าปริยาย 2.4 MHz ใช้ไม่ได้)
4. ความถี่ **915.000 MHz** แล้วกด Play
5. NFM เริ่ม bandwidth ประมาณ 12.5 kHz

ถ้าไม่มี RTL-TCP ให้เปิดโมดูล `rtl_tcp_source` ใน Module Manager
ไม่ต้องลงปลั๊กอิน Nomad แยก

### สิ่งที่ควรรู้ตอนดูน้ำตก

- ค่า **250 kHz ใน GUI เป็น interpolation บน PC** การรับจริงผ่าน USB คือ LID8 **31.25 kS/s**
- จูนความถี่ใหม่มีช่วงว่างประมาณ 1–2 วินาที โปรแกรมจะไม่เติมตัวอย่างปลอม
- เมนู gain / bias-tee ของ RTL-SDR ไม่ได้ควบคุมวงจร Nomad
  ปรับความดังฝั่ง PC ด้วย `--gain-db` ของตัวเชื่อม (ปริยาย 60 ถ้าล้นให้ลด)
- ไฟเขียว = กำลังส่ง I/Q, เหลือง = คิวเริ่มหนา, แดง = มี error

บันทึกไฟล์สั้นๆ โดยไม่เปิด GUI:

```powershell
python host/nomad_rx.py --port COM3 --radio 0 --decimate --frequency 915000000 --seconds 8 --output capture.cf32
```

ไฟล์เป็น complex float32 little-endian เปิดใน GNU Radio ได้ อ่าน sample rate จากไฟล์ `.json` คู่กัน

---

## ใช้ผ่าน Wi-Fi

เมื่อ PC ไม่มี USB ยาวพอ หรืออยากให้ I/Q วิ่งบนเครือข่าย

### โหมด AP (Nomad เป็นฮอตสปอต)

1. ต่อ Wi-Fi ของ PC เข้า SSID **Nomad-SDR** รหัส **nomadsdr1121**
2. IP ของบอร์ดคือ `192.168.4.1`
3. ดับเบิลคลิก `Start-Nomad-SDR.cmd` หรือ:

```powershell
python host/nomad_rtl_tcp.py --host 192.168.4.1 --radio 0 --port 1234
```

4. ใน SDRangel / SDR++ ชี้ไปที่ `127.0.0.1:1234` เหมือน USB

ชิป 1: ดับเบิลคลิก `Start-Nomad-Radio1.cmd` (พอร์ต PC 1235, ความถี่เริ่ม 2440 MHz)
บนบอร์ดชิป 0 ฟัง TCP **1121** ชิป 1 ฟัง **1122**

### โหมด STA (Nomad ต่อเราเตอร์บ้าน)

ตั้งค่าได้เฉพาะ USB ไม่รับจาก TCP และห้ามตั้งระหว่างสตรีม I/Q:

```powershell
python host/bridge.py --port COM3 --radio 0 wifi sta "SSID" "PASSWORD"
python host/bridge.py --port COM3 --radio 0 wifi
```

รอจน `connected` เป็น true แล้วใช้ค่า `ip` แทน `192.168.4.1`
PC ต้องอยู่ในเครือข่ายเดียวกัน (สาย LAN ก็ได้)

```powershell
python host/nomad_rtl_tcp.py --host THE_IP --radio 0 --port 1234
```

กลับเป็นฮอตสปอต: `python host/bridge.py --port COM3 --radio 0 wifi ap`
รหัสผ่านไม่ถูกพิมพ์ในคำตอบ และห้ามใส่ SSID จริงลง git

---

## Control API (สแกน / จับแพ็กเก็ต)

ใช้เมื่อต้องการ RSSI ทีละช่อง, มอนิเตอร์ LoRa/GFSK, CAD, เกน, อุณหภูมิชิป
**ปิดหน้าต่าง USB proxy ก่อน** แล้วดับเบิลคลิก `Start-Nomad-API.cmd` หรือ:

```powershell
python host/nomad_api.py --serial COM3
```

API อยู่ที่ `http://127.0.0.1:8094/api/v1`
กด Ctrl+C เพื่อหยุดและคืน COM3
คำตอบปกติเป็น `{ "ok": true, "result": ... }`
ผิดพารามิเตอร์ = 400, ไม่พบเส้นทาง/งาน = 404, ชิปไม่ว่าง = 409, พูดกับบอร์ดไม่ได้ = 502

ตั้งตัวช่วยใน PowerShell:

```powershell
$nomadApi = 'http://127.0.0.1:8094/api/v1'
Invoke-RestMethod "$nomadApi/capabilities"

function Send-Nomad($route, $payload) {
    Invoke-RestMethod "$nomadApi/$route" -Method Post -ContentType 'application/json' -Body ($payload | ConvertTo-Json -Depth 8)
}
```

`{r}` คือ `0` หรือ `1` ทุก POST ส่ง JSON object เส้นทาง start/stop ใช้ `{}`

| Method | เส้นทางใต้ `/api/v1` | ใช้ทำอะไร |
| --- | --- | --- |
| GET | `/capabilities` | เวอร์ชัน/UID สองชิป, modem, bandwidth |
| GET | `/radios/{r}/status` | โปรไฟล์, เกน, งานที่กำลังรัน |
| GET | `/radios/{r}/stream/status` | คิว I/Q, bytes, throughput, loss |
| POST | `/radios/{r}/rx/configure` | ตั้ง LoRa หรือ GFSK แล้วเข้า standby |
| POST | `/radios/{r}/rx/start` | เริ่มรับแพ็กเก็ตต่อเนื่อง |
| POST | `/radios/{r}/rx/stop` | หยุดแล้วเข้า standby |
| POST | `/radios/{r}/sweep/start` | สแกน RSSI ทีละช่องในพื้นหลัง |
| GET | `/radios/{r}/sweep/status` | ความคืบหน้าและค่า min/mean/max |
| POST | `/radios/{r}/sweep/stop` | ยกเลิกสแกน |
| POST | `/radios/{r}/packet/configure` | ตั้งโปรไฟล์แพ็กเก็ต |
| POST | `/radios/{r}/packet/start` | มอนิเตอร์แพ็กเก็ตในพื้นหลัง |
| GET | `/radios/{r}/packet/status` | payload, CRC, RSSI/SNR |
| POST | `/radios/{r}/packet/stop` | ยกเลิกมอนิเตอร์ |
| POST | `/radios/{r}/cad` | ตรวจ LoRa activity ครั้งเดียว |
| GET/POST | `/radios/{r}/gain` | AGC / step, RxBoosted, ขาเข้า LF0 |
| GET | `/radios/{r}/diagnostics` | อุณหภูมิไดและแรงดัน LR1121 |
| POST | `/dual/configure` | เก็บแผนสองชิป (sweep/packet) |
| POST | `/dual/start` | เริ่มแผน |
| GET | `/dual/status` | สถานะสองชิป |
| POST | `/dual/stop` | หยุดทั้งสองชิป |
| GET | `/jobs/{id}` | อ่านผลงานที่ยังอยู่ในหน่วยความจำ |
| GET | `/jobs/{id}.csv` | ดาวน์โหลด CSV |

### ตัวอย่าง: สแกนย่าน 902–928 MHz แล้วเซฟ CSV

```powershell
$job = Send-Nomad 'radios/0/sweep/start' @{ start_hz=902000000; stop_hz=928000000; step_hz=1000000; dwell_ms=10; samples=4; cycles=1; capacity=4096 }
Invoke-RestMethod "$nomadApi/radios/0/sweep/status"
Invoke-WebRequest "$nomadApi/jobs/$($job.result.id).csv" -OutFile 'sweep.csv'
Send-Nomad 'radios/0/sweep/stop' @{}
```

สแกนทีละช่อง ไม่ใช่ FFT ทั้งย่านพร้อมกัน สัญญาณสั้นอาจพลาดได้
`cycles=0` ทำซ้ำจนกว่าจะสั่งหยุด สูงสุด 4096 ช่องต่อรอบ

### ตัวอย่าง: รับ LoRa แล้วอ่าน diagnostics

```powershell
Send-Nomad 'radios/0/rx/configure' @{ modem='lora'; frequency_hz=915000000; sf=7; bandwidth_hz=125000; sync_word=18 }
Send-Nomad 'radios/0/rx/start' @{}
Send-Nomad 'radios/0/gain' @{ agc=$true; rx_boosted=$true; lna='differential' }
Invoke-RestMethod "$nomadApi/radios/0/diagnostics"
Send-Nomad 'radios/0/rx/stop' @{}
```

LoRa ต่ำกว่า 2300 MHz ใช้ bandwidth 125000 / 250000 / 500000
ย่าน 2.4 GHz ใช้ 203125 / 406250 / 812500 และชิป 1

### ตัวอย่าง: มอนิเตอร์ GFSK และ CAD

```powershell
Send-Nomad 'radios/0/packet/start' @{
    profile = @{ modem='gfsk'; frequency_hz=915000000; bit_rate=50000; deviation_hz=25000; bandwidth_hz=156200; sync_word='12345678' }
    duration_s = 10; poll_ms = 10; capacity = 256
}
Invoke-RestMethod "$nomadApi/radios/0/packet/status"
Send-Nomad 'radios/0/packet/stop' @{}

Send-Nomad 'radios/1/rx/configure' @{ modem='lora'; frequency_hz=2440000000; sf=7; bandwidth_hz=203125 }
Send-Nomad 'radios/1/cad' @{ symbols=2; detect_peak=22; detect_min=10; timeout_ms=1000 }
```

API นี้ถอด PHY อย่าง LoRa/GFSK ไม่ถอด LoRaWAN ที่เข้ารหัส และไม่ไล่ ELRS hopping ให้เอง
CAD บอกว่ามี activity ตาม threshold ที่ตั้ง ไม่ได้แปลว่าถอดแพ็กเก็ตสำเร็จ

### ตัวอย่าง: สองชิปพร้อมกัน (สแกน + จับแพ็กเก็ต)

```powershell
Send-Nomad 'dual/configure' @{ radios=@(
    @{ mode='sweep'; settings=@{ start_hz=902000000; stop_hz=928000000; step_hz=1000000; cycles=0 } },
    @{ mode='packet'; settings=@{ profile=@{ modem='lora'; frequency_hz=2440000000 } } }
) }
Send-Nomad 'dual/start' @{}
Invoke-RestMethod "$nomadApi/dual/status"
Send-Nomad 'dual/stop' @{}
```

โหมด dual ของ API คือแบ่งงาน sweep/packet บน UART เดียว มีล็อกกันคำสั่งสลับชิป
**ไม่ใช่** การส่ง I/Q สองช่องพร้อมกันเข้า SDRangel

ฟิลด์ครบและขอบเขตผลทดสอบอยู่ที่ [docs/control-api.md](docs/control-api.md)
Telemetry ทาง UART โดยไม่เปิด HTTP: `python host/bridge.py --port COM3 --radio 0 capabilities`

---

## ความถี่และเสาอากาศ

ซินธิไซเซอร์จูน **150–2500 MHz** ได้ทั้งสองชิป นั่นคือช่วงจูน ไม่ใช่คำรับรองความไวเท่ากันทุกย่าน

| ย่าน | ความหมายในการใช้จริง |
| --- | --- |
| 150–960 MHz | ย่าน RX ตามสเปก เสา/วงจร Nomad ดีสุดแถว 900 MHz — เริ่มที่ **915 MHz** |
| 1900–2200 MHz | ย่าน RX ตามสเปก |
| 2400–2500 MHz | ย่าน RX ตามสเปก เสา 2.4 GHz — เริ่มที่ **2440 MHz** |
| ช่องว่าง 960–1900 และ 2200–2400 MHz | จูนได้ (เคยลอง 1090, 1550, 2300) ให้ถือว่าเป็นการทดลอง |
| ต่ำกว่า 150 MHz | นอกช่วง FM 88–108 MHz ใช้ไม่ได้ |
| สูงกว่า 2500 MHz | นอกช่วง |

การจูน 1090 MHz ได้ไม่ได้แปลว่าถอด ADS-B เต็มแบนด์ได้ เพราะแบนด์วิดท์ native แคบ

ไฟ RGB (ความสว่างเต็ม, LED0 = ชิป 0, LED1 = ชิป 1):

| สี | ความหมาย |
| --- | --- |
| น้ำเงิน | พร้อมใช้ |
| เขียว | กำลังรับ I/Q |
| เหลือง | คิวเต็มอย่างน้อย 1/4 |
| แดง | DMA / คิว / วิทยุผิดพลาด |

```powershell
python host/bridge.py --port COM3 --radio 0 fan auto
python host/bridge.py --port COM3 --radio 0 led auto
```

`fan auto` อ่านอุณหภูมิได ESP32 ไม่ใช่ได LR1121 ค่า diagnostics ใน API เป็นคนละเซ็นเซอร์

---

## แฟลชเฟิร์มแวร์และคืน ExpressLRS

แฟลชเฉพาะ ESP32 **ตัวหลัก** ผ่าน CP210x ปล่อยสาย backpack ไว้

```powershell
python -m pip install platformio -r host/requirements.txt -r host/requirements-live.txt
python tools/test_nomad.py
python tools/build_nomad.py
```

แฟลชอิมเมจรวมที่ offset `0x0`:

```powershell
python -m platformio pkg exec -p tool-esptoolpy -- esptool.py --chip esp32 --port COM3 write_flash 0x0 dist/nomad/nomad-sdr-merged.bin
```

รันจากโฟลเดอร์ `nomad/` หรือใส่พาธเต็มไปที่ `nomad-sdr-merged.bin`

คืน ExpressLRS: `python lr1121/install.py restore-elrs` คู่กับ backup เต็มจาก `build/backups/`
อย่าแฟลช LR1121 เป็น 0x0104 / 0x0105 / Modem-E ถ้ายังต้องการเส้นทาง SDR ปัจจุบัน (0x0103)

---

## ปัญหาที่พบบ่อย

| อาการ | สิ่งที่ตรวจ |
| --- | --- |
| `Access is denied` / พอร์ตไม่ว่าง | ปิด API, USB proxy, SDRangel, Serial Monitor ให้เหลือโปรแกรมเดียว |
| `info` ไม่ขึ้น หรือ baud ผิด | ใช้พอร์ตตัวหลัก CP210x ที่ 921600 ไม่ใช่ backpack |
| SDR++ ไม่มีภาพ | ต้องเลือก 250 kHz ก่อน Play ค่า 2.4 MHz ใช้ไม่ได้ |
| Waterfall กระตุกตอนจูน | ปกติประมาณ 1–2 วินาที ระหว่างรีเซ็ตวงจรรับ |
| เปิด API แล้ว waterfall ดับ | COM3 ใช้ร่วมกันไม่ได้ ปิดอันหนึ่งก่อนเปิดอีกอัน |
| ไม่มีสัญญาณที่ 915 MHz | ตรวจเสา 900 MHz, จูนชิป 0, ดูว่าไฟเป็นเขียวตอน Start |
| 2.4 GHz ขาดหาย | ยังไม่รับรองสตรีมต่อเนื่องในย่านนี้ ลองชิป 1 ช่วงสั้นก่อน |
| STA ไม่ได้ IP | รอแล้วเรียก `wifi` อีกครั้ง ถ้าเกิน 20 วินาทีบอร์ดจะเปิด AP สำรอง |

ตรวจโปรโตคอล USB โดยไม่เปิด GUI (ไม่จูน RF อ้างอิง):

```powershell
python tools/smoke_nomad_live.py --serial COM3 --radio 0 --seconds 60
```

ผลอยู่ที่ `build/live-smoke.json`

---

## ข้อจำกัด

- USB ส่ง I/Q ได้ทีละชิป ที่ 31.25 kS/s (LID8) ค่า 250 kHz ในโปรแกรมเป็นภาพขยายบน PC
- Control API เป็น RX เท่านั้น งาน dual แชร์ UART ไม่ใช่ dual I/Q
- Packet / CAD ยังไม่มีเครื่องส่งอ้างอิงยืนยันความไวหรือโอกาสตรวจพบ
- Wi-Fi ต่อเนื่องที่ย่าน 2.4 GHz และ I/Q สองชิปพร้อมกันยังต้องวัดเพิ่ม
- ความไว นอกย่านเสา 900 / 2.4 GHz ยังไม่พิสูจน์
- [Packed ARC](docs/packed-stream.md) เป็นทางทดลองของชิป 1 เปิดด้วย `--packed-verification` ค่าปริยายยังเป็นทางรับปกติ
- เส้นทาง Pico LIP2/LIP3 250/500 kS/s, TX และโมดูล SDR++ ของบอร์ด RP2040 ยังอยู่ที่ต้นน้ำ

---

## โครงสร้างโฟลเดอร์

- `nomad/` — เฟิร์มแวร์ ESP32 (PlatformIO, MIT)
- `host/` — สะพาน UART/TCP, ตัวบันทึก, rtl_tcp, JSON API (`nomad_api.py`)
- `pico/` — เฟิร์มแวร์ RP2040 ต้นทาง [lr1121-sdr](https://github.com/naorunaoru/lr1121-sdr)
- `sdrpp/` — โมดูล SDR++ ของ Pico (GPLv3)
- `docs/` — คู่มือฮาร์ดแวร์, live SDR, API, ผลการวัด

## ผู้พัฒนา

[hereismeaw](https://github.com/hereismeaw)

## สัญญาอนุญาต

ต้นทาง [naorunaoru/lr1121-sdr](https://github.com/naorunaoru/lr1121-sdr)
แผนขาจาก [ExpressLRS Nomad](https://github.com/ExpressLRS/targets)
สายงานวิจัย LR1121 รวม [radioegor146/lr-semtech-research](https://github.com/radioegor146/lr-semtech-research)

เฟิร์มแวร์ เครื่องมือโฮสต์ และเอกสารอิสระ: [MIT](LICENSE)
`sdrpp/` และตัวช่วยรับที่ดัดแปลงจากโมดูลนี้: [GPLv3](sdrpp/LICENSE)
ดู [ขอบเขตสัญญา](docs/licensing.md) และ [third-party notices](THIRD_PARTY_NOTICES.md)
อิมเมจ Semtech LR1121 ใช้สัญญาของผู้ขาย ห้าม commit `nomad/src/wifi.local.h`
