# ใช้ RadioMaster Nomad กับ SDR++ / SDRangel

เฟิร์มแวร์ Nomad 0.4.0 เพิ่ม **LIQ8** สำหรับรับ I/Q ต่อเนื่องผ่าน LAN/Wi-Fi
รุ่น 0.7.0 ใช้พัดลมตามอุณหภูมิได ESP32 และ RGB ความสว่างเต็มตามสถานะ ดู [คู่มือ Nomad](nomad.md)
และ `host/nomad_rtl_tcp.py` แปลงเป็นโปรโตคอล **rtl_tcp / RTL0** บน PC
รองรับ Windows, ชิป 0 หรือ 1, จูนความถี่จากโปรแกรม, PPM และ sample rate ฝั่ง PC

## เริ่มใช้งาน

ติดตั้ง dependencies ครั้งแรกจาก PowerShell ในโฟลเดอร์ repo:

```powershell
python -m pip install -r host/requirements-live.txt
```

USB native: ดับเบิลคลิก `Start-Nomad-USB.cmd` หรือ

```powershell
python host/nomad_rtl_tcp.py --serial COM3 --radio 0 --port 1234
```

Wi-Fi: ดับเบิลคลิก `Start-Nomad-SDR.cmd` (ค่าเริ่ม AP `192.168.4.1`) หรือส่ง `--host` เป็น IP จาก `wifi`

```powershell
python host/nomad_rtl_tcp.py --host 192.168.4.1 --radio 0 --port 1234
```

ปล่อยหน้าต่างตัวเชื่อมเปิดไว้ที่ **127.0.0.1:1234**; กด Ctrl+C เพื่อหยุด
ตัวเชื่อมจะติดต่อ Nomad เมื่อมีโปรแกรม SDR เชื่อมเข้ามาเท่านั้น
ห้ามเปิดตัวเชื่อมซ้ำบนพอร์ตเดียวกัน

หาก IP ของ Nomad เปลี่ยน ให้ดูจาก `bridge.py --port COM3 --radio 0 wifi`
แล้วเปลี่ยน `--host` ในคำสั่งหรือไฟล์ `.cmd`
ตั้ง SSID/รหัสผ่าน STA ใหม่ได้จาก UART: `bridge.py --port COM3 --radio 0 wifi sta "SSID" "PASSWORD"`

## SDR++

1. ใน Source เลือก **RTL-TCP**
2. ตั้ง Host **127.0.0.1**, Port **1234** (หรือ **1235** สำหรับชิป 1)
3. เลือก sample rate **250 kHz** ก่อน Start
4. ตั้งความถี่ เช่น **915.000 MHz** แล้วกด Play
5. เลือก demodulator NFM, AM, USB/LSB ตามชนิดสัญญาณ; สำหรับ NFM เริ่ม bandwidth 12.5 kHz

หากไม่มี RTL-TCP ในรายการ ให้เปิด module `rtl_tcp_source` ใน Module Manager
Source นี้มีใน upstream SDR++ ไม่ต้องลง plugin Nomad เฉพาะทาง

## SDRangel

1. เพิ่ม Rx device แล้วเลือก **Remote TCP Input**
2. Server **127.0.0.1**, Port **1234** (หรือ **1235** สำหรับชิป 1)
3. Protocol เลือก **SDRangel**; ตัวรับตรวจ header แล้วใช้ **RTL0** อัตโนมัติ
4. Device sample rate และ Channel sample rate **250000**, decimation **1 / log2Decim 0**,
   sample bits **8**, เปิด **Override remote settings**
5. ตั้ง center frequency **915000000 Hz** แล้ว Start; เพิ่ม channel **NFM Demodulator**
   หรือ demodulator ที่ต้องการ

SDRangel เลือก rate **62500** หรือ **125000** ได้ด้วย หากต้องการแสดงตาม rate ต่ำกว่า
ใช้ pre-fill ประมาณ **0.1–1 s** เพื่อรองรับ jitter เครือข่าย

## ความถี่และคุณภาพข้อมูล

- เปิดช่วงจูน synthesizer **150–2500 MHz แบบต่อเนื่อง** บนชิปทั้งสองตัว
  ตาม datasheet ตาราง 3-7 ช่วงนี้ไม่ได้หมายถึง RF sensitivity คงที่ตลอดช่วง
- ย่าน RX ที่มีสเปกผู้ผลิตคือ **150–960**, **1900–2200** และ **2400–2500 MHz**
  ช่วงคั่นกลาง เช่น **1090 MHz** และ **1550 MHz** ใช้เป็นการทดลอง SDR เท่านั้น
  วงจร matching/เสาอากาศของ Nomad ยังเหมาะกับ 900 MHz และ 2.4 GHz
- FM broadcast **88–108 MHz** ต่ำกว่าขอบเขตนี้ และยังไม่รองรับ
- Native acquisition **62.5 kS/s**; LIQ8 ใช้ signed 8-bit I/Q พร้อม scale ต่อ block
  แล้วถอดกลับเป็น float บน PC เป็นการลดความละเอียดจาก LIQ1 23-bit
- ที่ GUI 250 kS/s ตัวเชื่อมทำ FIR interpolation ×4 บน PC เพื่อให้ตรงกับรายการ
  sample rate ของ SDR++: **ไม่ได้เพิ่ม RF bandwidth** หรือความละเอียด RF
- มีการตรวจ header CRC, payload CRC, sequence และ terminal counters จาก Nomad
  หาก acquisition สูญหาย ตัวเชื่อมปิดการเชื่อมต่อและบันทึก error ไม่เติม sample ปลอม
- ระหว่างจูนใหม่ต้องหยุด/ตั้งค่า LR1121 และเริ่ม ring ใหม่ จึงมีช่วงว่างประมาณ 1–2 s
- LR1121 ใช้ hardware AGC; เมนู gain/AGC/bias-tee/direct-sampling ของ RTL-SDR
  ไม่ได้ควบคุมวงจร RTL2832 เพราะ Nomad ไม่มีวงจรนั้น ตัวเชื่อม log คำสั่งที่ไม่ได้รองรับ
- Gain ฝั่ง PC ตั้งด้วย `--gain-db` (ปริยาย 60 dB); ถ้าสัญญาณล้นให้ลดค่า
  ค่า gain นี้ไม่ใช่ calibrated RF gain และไม่มีการจ่ายไฟ bias tee
- อย่าให้ capture CLI, ตัวเชื่อม และโปรแกรมอื่นควบคุมชิปเดียวกันพร้อมกัน
- รายงาน runtime อยู่ที่ `build/rtl-tcp-status.json`; log ในหน้าต่างตัวเชื่อม

โปรโตคอล RTL0 ไม่มีข้อความตอบกลับการจูน: หากเลือกความถี่หรือ sample rate
ที่ไม่รองรับ ตัวเชื่อมแจ้งเหตุผลใน log และตัดการเชื่อมต่อ ให้แก้ค่าก่อน Start ใหม่
SDR++ ต้องเลือก **250 kHz**; ค่า 2.4 MHz ปริยายของ RTL-TCP ไม่รองรับ

## ผลทดสอบบนเครื่องนี้

- Firmware 0.4.0: ชิป 0 และ 1 รับ LIQ8 ที่ 915 MHz ต่อเนื่อง 8 s ได้ชิปละ
  500,000 complex samples, CRC/sequence ผ่าน, `flags=0`, `lost_samples=0`
- ทดสอบ rtl_tcp header, คำสั่งแบบแบ่งแพ็กเก็ต, การจูน 915/916/2440 MHz,
  การเชื่อมต่อซ้ำ และ FIR interpolation พร้อม unit tests
- SDRangel **7.25.1** เชื่อม Remote TCP Input ได้จริงที่ 250000 S/s,
  DSP ขึ้น `running` และ NFM Demodulator ประมวลผล I/Q ได้
- การจูน/อ่าน I/Q ช่วงสั้นบนทั้งสองชิปผ่าน **26/26** กรณี: 150, 300, 433,
  868, 960, 1090, 1550, 1900, 2100, 2200, 2300, 2400, 2500 MHz
  ดู `build/wideband-hardware/results.json` ผลนี้ไม่มี RF reference tone ป้อนเข้า
- **ข้อจำกัดที่พบจริง:** capture ต่อเนื่องที่ 2440/2470 MHz บางรอบยัง queue-full
  แม้เป็น LIQ8 จึงยังไม่รับรองความต่อเนื่องใน 2.4 GHz หรือสองช่องพร้อมกัน
  ยังไม่ยืนยันสาเหตุ; Wi-Fi กับ RF ย่านนี้อาจกระทบกันได้
- SDR++ ตรวจความเข้ากันได้จาก source และ rtl_tcp wire test;
  ยังไม่ได้รัน GUI ของ SDR++ บน PC เครื่องนี้

การจูน 1090 MHz ได้ไม่ได้ทำให้รับ ADS-B แบบเต็มแบนด์ได้: native I/Q และ
แบนด์วิดท์ของ LR1121 ยังจำกัด การ upsample เป็น 250 kS/s ไม่เพิ่มแบนด์วิดท์จริง

## แหล่งอ้างอิงโปรโตคอล

- [SDR++ RTL-TCP source และ sample rate](https://github.com/AlexandreRouma/SDRPlusPlus/blob/master/source_modules/rtl_tcp_source/src/main.cpp)
- [SDRangel Remote TCP Input](https://github.com/f4exb/sdrangel/blob/master/plugins/samplesource/remotetcpinput/readme.md)
- [rtl_tcp header และ command framing](https://github.com/osmocom/rtl-sdr/blob/master/src/rtl_tcp.c)

ตัวเชื่อมใช้ GPL-3.0-only ตาม receiver helper ที่นำมาใช้ เฟิร์มแวร์ `nomad/` ใช้ MIT
