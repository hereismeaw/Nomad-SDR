# Nomad control API

เฟิร์มแวร์ **0.11.0** เพิ่ม native `capabilities` และ `stream status`
พร้อม control API บน PC สำหรับ RX, sweep, packet, CAD, gain, diagnostics และ dual mode
ใช้ Python standard library เพิ่มเติมจาก dependencies ของโปรเจกต์เดิม

## เริ่มใช้

ปิดโปรแกรมที่เปิด COM3 อยู่ แล้วดับเบิลคลิก `Start-Nomad-API.cmd` หรือรัน:

```powershell
python host/nomad_api.py --serial COM3
```

API อยู่ที่ `http://127.0.0.1:8094/api/v1` กด Ctrl+C เพื่อหยุดงานและปิดการเชื่อมต่อ
กรณี TCP ใช้ `--host` แทน `--serial` โดยระบุ IP ที่อ่านจากคำสั่ง `wifi`

API server ถือ COM3 ระหว่างทำงาน จึงต้องปิด server ก่อนเปิด USB I/Q proxy
หรือ recorder อีกตัว การแบ่งสองชิปของ control API ใช้การสลับ radio อย่างมี lock
บน UART เดียว ไม่ใช่การส่ง dual I/Q พร้อมกันผ่าน USB

```powershell
$nomadApi = 'http://127.0.0.1:8094/api/v1'
Invoke-RestMethod "$nomadApi/capabilities"

function Send-Nomad($route, $payload) {
    Invoke-RestMethod "$nomadApi/$route" -Method Post -ContentType 'application/json' -Body ($payload | ConvertTo-Json -Depth 8)
}
```

คำตอบ JSON ปกติเป็น `{ "ok": true, "result": ... }`
ข้อผิดพลาดใช้ HTTP 400 สำหรับพารามิเตอร์, 404 สำหรับ route/job ที่ไม่มี,
409 เมื่อมีงานอื่นถือ radio และ 502 เมื่อสื่อสารกับบอร์ดไม่สำเร็จ

## API ที่เพิ่มครบ

`{r}` คือ `0` หรือ `1` ทุก POST ใช้ JSON object

| Method | Path ใต้ `/api/v1` | หน้าที่ |
| --- | --- | --- |
| GET | `/capabilities` | เวอร์ชัน/UID ของสองชิป, modems, bandwidths, rates และข้อจำกัด transport |
| GET | `/radios/{r}/status` | สถานะที่ controller จัดการ, profile, gain และ job |
| GET | `/radios/{r}/stream/status` | Native I/Q counters, queue estimate, flags, bytes, throughput และ loss indicator |
| POST | `/radios/{r}/rx/configure` | ตั้ง LoRa/GFSK และจบใน standby |
| POST | `/radios/{r}/rx/start` | เริ่ม continuous packet RX ตาม profile; body `{}` |
| POST | `/radios/{r}/rx/stop` | ยกเลิกงานและเข้า standby; body `{}` |
| POST | `/radios/{r}/sweep/start` | เริ่มงาน RSSI scan เบื้องหลัง |
| GET | `/radios/{r}/sweep/status` | ผลสแกนและความคืบหน้า |
| POST | `/radios/{r}/sweep/stop` | ขอยกเลิก sweep; body `{}` |
| POST | `/radios/{r}/packet/configure` | ตั้ง packet profile เช่นเดียวกับ rx/configure |
| POST | `/radios/{r}/packet/start` | เริ่ม packet monitor เบื้องหลัง |
| GET | `/radios/{r}/packet/status` | payload, CRC, RSSI/SNR, counters และสถานะงาน |
| POST | `/radios/{r}/packet/stop` | ขอยกเลิก packet monitor; body `{}` |
| POST | `/radios/{r}/cad` | ทำ LoRa CAD หนึ่งครั้ง; ไม่มี CAD-TX exit mode |
| GET/POST | `/radios/{r}/gain` | อ่าน desired gain หรือกำหนด AGC/manual step, RxBoosted และ LF0 topology |
| GET | `/radios/{r}/diagnostics` | อุณหภูมิได/แรงดัน LR1121, raw values และ chip errors |
| POST | `/dual/configure` | ตรวจและเก็บแผนงานสองชิป โดยยังไม่เริ่ม |
| POST | `/dual/start` | เริ่มแผนที่ตั้งไว้; body `{}` |
| GET | `/dual/status` | สถานะและผลสองชิป |
| POST | `/dual/stop` | หยุดทั้งสองชิป; body `{}` |
| GET | `/jobs/{id}` | อ่านผล job ที่ยังอยู่ในประวัติ |
| GET | `/jobs/{id}.csv` | ดาวน์โหลดผลที่ยังเก็บอยู่เป็น CSV |

Native telemetry ไม่ทำ SPI เพื่อ probe extension จึงไม่สรุปว่า extension ติดตั้ง
จากหมายเลข firmware เพียงอย่างเดียว การใช้ ARC streaming ยังต้องผ่านไฟล์
ผูกชิปและ callback verification ตาม [packed streaming](packed-stream.md)

## RX และ gain

```powershell
Send-Nomad 'radios/0/rx/configure' @{ modem='lora'; frequency_hz=915000000; sf=7; bandwidth_hz=125000; sync_word=18 }
Send-Nomad 'radios/0/rx/start' @{}
Send-Nomad 'radios/0/gain' @{ agc=$false; step=4; rx_boosted=$true; lna='differential' }
Send-Nomad 'radios/0/gain' @{ agc=$true; rx_boosted=$false }
Invoke-RestMethod "$nomadApi/radios/0/diagnostics"
Send-Nomad 'radios/0/rx/stop' @{}
```

LoRa รับ `sf` 5..12, `coding_rate` 5..8 (ตัวส่วนของ 4/x), `preamble`,
`sync_word` แบบเลข 0..255, `crc`, `implicit`, `iq_inverted`, `payload_length`
bandwidth ต่ำกว่า 2300 MHz ใช้ 125000/250000/500000 Hz
ช่วงสูงใช้ 203125/406250/812500 Hz ค่าเหล่านี้เป็นขอบเขตของ API profile
ไม่ใช่คำยืนยัน sensitivity ตลอดช่วง synthesizer 150..2500 MHz

GFSK ใช้ `bit_rate` 2400..300000, `deviation_hz`, `bandwidth_hz` จาก capabilities,
`preamble`, `sync_word` เป็น hex 1..8 bytes, `crc`, `whitening`, `payload_length`,
`crc_seed`, `crc_polynomial`, `whitening_seed` bandwidth ต้องครอบคลุม bitrate + 2*deviation
โหมด 600/1200 bit/s ที่ต้องใช้ workaround ยังไม่รวมใน API นี้

`lna` รับ `differential`, `single_n`, `single_p` เป็น topology ของ LF0
ไม่ใช่ระดับ gain เพิ่มเติมหรือการเลือกเสาอากาศบน Nomad โดยอัตโนมัติ
manual `step` เป็นดัชนี register 0..15 ไม่ใช่ dB มี readback ตรวจสถานะ
และคืน AGC control จากค่าหลัง reset เมื่อเปิด AGC กลับ
ผลด้านความไวและ clipping ยังต้องวัดด้วยสัญญาณอ้างอิง

diagnostics เป็นค่าโดยประมาณจากสูตร Semtech/Vana nominal 1.35 V
controller พัก RX ชั่วครู่แล้วคืนสถานะเดิม; จะปฏิเสธขณะมี sweep/packet job
พัดลม Auto ยังคงใช้อุณหภูมิ ESP32 ตามเดิม

## RSSI sweep และ CSV

```powershell
$job = Send-Nomad 'radios/0/sweep/start' @{ start_hz=902000000; stop_hz=928000000; step_hz=1000000; dwell_ms=10; samples=4; cycles=1; capacity=4096 }
Invoke-RestMethod "$nomadApi/radios/0/sweep/status"
Invoke-WebRequest "$nomadApi/jobs/$($job.result.id).csv" -OutFile 'sweep.csv'
Send-Nomad 'radios/0/sweep/stop' @{}
```

`cycles=0` หมายถึงทำซ้ำจนสั่งหยุด จำกัด 4096 ช่องต่อรอบ
ผลมี frequency, min/mean/max RSSI, จำนวน samples, cycle และ timestamp
`dwell_ms` เป็นเวลารอขั้นต่ำหลังจูน; ความเร็วจริงยังรวมคำสั่ง SPI/UART
การสแกนทำทีละช่อง จึงอาจพลาดสัญญาณสั้น และไม่ได้เป็น FFT พร้อมกันทั้งย่าน
สามารถส่ง `profile` เป็น LoRa/GFSK profile ที่ต้องการใช้เป็น filter

## Packet monitor และ CAD

```powershell
Send-Nomad 'radios/0/packet/start' @{ profile=@{ modem='gfsk'; frequency_hz=915000000; bit_rate=50000; deviation_hz=25000; bandwidth_hz=156200; sync_word='12345678' }; duration_s=10; poll_ms=10; capacity=256 }
Invoke-RestMethod "$nomadApi/radios/0/packet/status"
Send-Nomad 'radios/0/packet/stop' @{}

Send-Nomad 'radios/1/rx/configure' @{ modem='lora'; frequency_hz=2440000000; sf=7; bandwidth_hz=203125 }
Send-Nomad 'radios/1/cad' @{ symbols=2; detect_peak=22; detect_min=10; timeout_ms=1000 }
```

`duration_s=0` เป็น packet monitor ต่อเนื่อง ผลมี payload_hex, RSSI/SNR ตาม PHY,
IRQ และ CRC status; ถ้า packet ไม่มี CRC จะรายงาน `crc_ok=null`
LoRa explicit-header อ่าน CRC presence จาก header จริง ไม่อ้างจากค่าที่ตั้งอย่างเดียว
receiver พักรับระหว่างคัดลอก packet buffer เพื่อไม่อ่าน payload ที่กำลังถูกเขียนทับ
การรับเร็วกว่าเวลาที่ host poll/copy ทันอาจทำให้พลาด packet

`buffer_evictions` นับเฉพาะผลเก่าที่ถูกลบจากบัฟเฟอร์ PC
`hardware_drops=null` หมายถึงยังวัดจำนวน packet ทาง RF ที่พลาดไม่ได้
CRC/header error counters เป็น events ที่ host เห็น ไม่ใช่จำนวน packet ที่เครื่องส่งส่งทั้งหมด
CAD `detected=true` เป็นการตรวจพบตาม SF/BW/threshold ที่ตั้ง ไม่ใช่การถอด packet
PHY monitor ไม่ได้ถอดรหัส LoRaWAN หรือไล่ตาม ELRS hopping อัตโนมัติ

## Dual mode

```powershell
Send-Nomad 'dual/configure' @{ radios=@(
    @{ mode='sweep'; settings=@{ start_hz=902000000; stop_hz=928000000; step_hz=1000000; cycles=0 } },
    @{ mode='packet'; settings=@{ profile=@{ modem='lora'; frequency_hz=2440000000 } } }
) }
Send-Nomad 'dual/start' @{}
Invoke-RestMethod "$nomadApi/dual/status"
Send-Nomad 'dual/stop' @{}
```

รองรับ sweep+sweep, packet+packet และ sweep+packet
การสลับ radio และ SPI request ใช้ lock ร่วม ป้องกันคำสั่งของสองงานสลับชิปผิด
ถ้าเริ่มงานตัวที่สองไม่สำเร็จ จะพยายามหยุดงานที่เริ่มไปแล้ว
สามารถสั่งหยุดแต่ละชิปผ่าน endpoint ของงานนั้นด้วย

## สถานะและขอบเขตผลทดสอบ

- Native `capabilities` / `stream status` ใช้ผ่าน bridge CLI ได้ด้วย:
  `python host/bridge.py --port COM3 --radio 0 capabilities` และ `stream-status`
- `stream/status` เป็น I/Q telemetry ของ firmware ไม่ใช่ผล sweep/packet
  queue เป็นค่าประมาณจาก produced-sent รวมข้อมูลที่รอส่งบางส่วน
  throughput เป็นค่าเฉลี่ยต่อ job จาก complete data frames ไม่รวม terminal frame
  snapshot counters อาจต่างเวลากันเล็กน้อยระหว่าง producer/consumer ทำงาน
- ขณะโปรแกรมอื่นถือ USB เพื่อส่ง binary I/Q จะเปิด COM3 ซ้ำไม่ได้
  ดู live report ของ rtl_tcp proxy ในกรณีนั้น หรือใช้ telemetry ผ่าน UART ขณะ I/Q อยู่บน TCP
- Job เก็บผลล่าสุดตาม `capacity` 1..4096 (ปริยาย 256) และประวัติสูงสุด 16 jobs ต่อ radio
  CSV ส่งเฉพาะผลที่ยังอยู่ในบัฟเฟอร์ เลือก capacity ให้พอกับ sweep ที่ต้องการเก็บ
- Hardware HTTP checks ผ่าน RX/LoRa/GFSK configuration, gain readback, diagnostics,
  CAD completion, sweep lifecycle และ dual sweep+packet บน COM3
  หลักฐาน: `build/api-hardware-final.json`
- Packet parser ทดสอบด้วย known vectors รวม signed SNR/CRC และ worker รับ packet จำลอง
  ยังไม่มีเครื่องส่งอ้างอิงสำหรับยืนยัน RF payload, CAD detection probability หรือ sensitivity

รันทดสอบบนบอร์ดอีกครั้งได้ด้วย:

```powershell
python tools/test_nomad_api_hardware.py --serial COM3
```

คำสั่งนี้เป็น RX-only และปิดการเชื่อมต่อเมื่อจบ ไม่มีการอัปเดต firmware ของ LR1121
