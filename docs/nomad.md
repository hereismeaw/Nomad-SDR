# RadioMaster Nomad SDR port

พอร์ตสำหรับ **ESP32 ตัวหลัก** ของ RadioMaster Nomad พร้อม LR1121 สองตัว
สถานะ: บิลด์และทดสอบ offline บน Windows และทดสอบ main ESP32/LR1121 ผ่าน USB แล้ว
ตรวจรายละเอียดผลจริงใน `build/nomad-hardware-validation.json` เมื่อมีไฟล์นี้
ยังไม่รับรองความไวรับสัญญาณ ความต่อเนื่องของ I/Q ระยะยาว หรือความเร็ว Wi-Fi สูงสุด

## สิ่งที่เพิ่ม

- เฟิร์มแวร์ Arduino/PlatformIO ใน `nomad/` ใช้ parser และ LIQ1 codec ร่วมกับ Pico
- Wi-Fi AP `Nomad-SDR`, รหัสผ่าน `nomadsdr1121`, IP `192.168.4.1`
- รองรับ STA ใน firmware 0.3.0: ต่อเราเตอร์เพื่อให้ PC ที่ใช้ LAN เข้าถึงได้
- LR1121 ตัวที่ 0 ใช้ TCP 1121, ตัวที่ 1 ใช้ TCP 1122; หนึ่งเจ้าของต่อชิป
- รับทีละชิปที่ 62.5/125 kS/s หรือสองชิปที่ **62.5 kS/s ต่อชิป**
- ตัวบันทึก Windows/Linux/macOS ใน `host/nomad_rx.py` ให้ไฟล์ `cf32_le`
  (float32 little endian สลับ I,Q) พร้อม metadata และผลตรวจ CRC/sequence/counters
- ตรวจ firmware identity, rate, PLL และ DMA layout/readback ก่อนติดตั้ง ring
- หยุดเมื่อ radio DMA ตามไม่ทัน, คิวเต็ม, BUSY timeout หรือการเชื่อมต่อขาด
- UART 921600 ผ่าน main ESP32/CP210x ใช้ควบคุม, provisioning และ USB native LID8
  LIQ1 ยังจำกัด 32 blocks; สตรีมต่อเนื่องใช้ compact บน USB หรือ TCP

สองช่องจูนอิสระและเริ่มจาก barrier ฝั่ง PC แต่ **ไม่ได้ซิงก์ sample clock/phase**
ห้ามตีความเป็น coherent MIMO หรือเอา sample index มาเทียบเวลาแบบแม่นยำข้ามชิป
อัตราสองช่องถูกจำกัดเพราะ SPI 16 MHz ใช้ร่วมกัน และ LIQ1 อ่านข้อมูล 8 bytes ต่อ complex sample
ก่อนย่อเหลือ 6 bytes บนเครือข่าย; 125 kS/s สองช่องเกินงบ SPI เมื่อรวม overhead

พอร์ตนี้ใช้ stock LR1121 **transceiver 1.3 (`22030103`)** ไม่ต้องลง ARC extension
รองรับ live SDRangel และ SDR++ ผ่านตัวเชื่อม rtl_tcp ตั้งแต่ 0.4.0;
ดู [คู่มือ live SDR](live-sdr.md) ยังไม่รองรับ LIP2/LIP3 250/500 kS/s, TX และ reset guard
โมดูล SDR++ เฉพาะทางเดิมยังเป็น serial/POSIX สำหรับ Pico; เปิดไฟล์ capture ด้วยโปรแกรม
ที่รองรับ raw complex float32 เช่น GNU Radio (File Source, Complex, sample rate ตาม metadata)

## ข้อมูลบอร์ดและแหล่งอ้างอิง

Pin mapping จาก [ExpressLRS Nomad target](https://github.com/ExpressLRS/targets/blob/master/TX/Radiomaster%20Nomad.json)
และรายละเอียด MCU จาก [RadioMaster](https://radiomasterrc.com/products/nomad-gemini-xrossband-expresslrs-module)
ตรวจเมื่อ 2026-11-04:

| สัญญาณ | LR1121 #0 | LR1121 #1 |
| --- | --- | --- |
| SCK / MOSI / MISO | 25 / 32 / 33 | ใช้ร่วมกัน |
| NSS | 27 | 13 |
| BUSY | 36 | 39 |
| RESET | 15 | 21 |
| DIO9 (ชื่อ `dio1` ใน ELRS) | 37 | 34 |

GPIO26 คือ PA APC, GPIO2 คือ fan enable, GPIO19 คือ backpack enable
GPIO22 คือ WS2812 จำนวน 2 ดวง ลำดับ GRB ตาม ExpressLRS `led_rgb` / `led_rgb_isgrb`
เฟิร์มแวร์ตั้ง PA APC ต่ำ ค้าง backpack ใน reset
GPIO34/36/37/39 ใช้ input โดยไม่มี internal pull-up/down

คำสั่งบอร์ดผ่าน UART หรือ TCP (ไม่ผูกชิปรadio):

```powershell
python host/bridge.py --port COM3 --radio 0 fan
python host/bridge.py --port COM3 --radio 0 fan auto
python host/bridge.py --port COM3 --radio 0 led
python host/bridge.py --port COM3 --radio 0 led auto
```

`fan auto` (ปริยาย) อ่านอุณหภูมิได ESP32: เปิดเมื่อ ≥ 50 °C ปิดเมื่อ ≤ 42 °C
`fan on` / `off` บังคับ ค่า `temp_c` ในคำตอบ `fan` เป็นอุณหภูมิได ไม่ใช่เซ็นเซอร์ RF
`led auto` ความสว่างเต็ม 255 และ LED0/LED1 ตามชิป:
น้ำเงิน = พร้อมใช้, เขียว = กำลังรับ I/Q, เหลือง = คิวเต็มอย่างน้อย 1/4 (buffered), แดง = DMA/คิว/วิทยุผิดพลาด
`led R G B` หรือ `led INDEX R G B` ล็อกสีจนกว่าจะ `led auto`

RF switch ใช้ค่าปริยายของ [ExpressLRS LR1121 driver](https://github.com/ExpressLRS/ExpressLRS/blob/master/src/lib/LR1121Driver/LR1121.cpp):
`0f 00 04 08 08 02 00 01` ไม่ใช้ค่าของ Waveshare
Nomad target ไม่มี TCXO/external LF-clock override จึงไม่ส่งคำสั่ง Waveshare 3 V TCXO/32 kHz
อ้างอิง driver snapshot `caf1ccd8199f22585dca727d75ad4f5e3c4c698d`
วงจร/PCB revision ของเครื่องจริงยังต้องตรวจยืนยันก่อนการทดสอบ RF

## Build และไฟล์แฟลช

รันที่ root ของ repo:

```powershell
python -m pip install platformio -r host/requirements.txt
git submodule update --init external/radio-firmware-images
python tools/build_nomad.py
python tools/test_nomad.py
```

ผลลัพธ์ใน `dist/nomad/`:

| ไฟล์ | offset สำหรับ main ESP32 |
| --- | --- |
| `nomad-sdr-merged.bin` | `0x0` (รวม bootloader/partition/boot_app0/application) |
| `firmware.bin` | `0x10000` (application สำหรับ partition ของพอร์ตนี้) |
| `manifest.json` | ขนาดและ SHA256 ของแต่ละไฟล์ |

PlatformIO pin ไว้ที่ Espressif32 6.12.0 / Arduino ESP32 2.0.17,
ESP32 240 MHz, flash 4 MB, DIO 40 MHz, default partition
ตรวจขนาด flash ของเครื่องก่อนใช้ merged image
แก้ SSID/password ได้ด้วย build defines `NOMAD_AP_SSID` / `NOMAD_AP_PASSWORD`

### ต่อเราเตอร์ด้วย STA (PC ใช้สาย LAN)

ตั้งค่าได้สองทาง ค่าที่บันทึกผ่าน UART อยู่ใน NVS และมีผลหลังรีบูต
คำสั่งตั้งค่าใช้ได้เฉพาะ USB/UART ไม่รับจาก TCP

```powershell
python host/bridge.py --port COM3 --radio 0 wifi
python host/bridge.py --port COM3 --radio 0 wifi sta "SSID" "PASSWORD"
python host/bridge.py --port COM3 --radio 0 wifi ap
```

รอสักครู่แล้วเรียก `wifi` อีกครั้งเพื่อดู `connected` และ `ip`
`wifi sta` ต้องมี token รหัสผ่าน; เครือข่ายเปิดใช้ `""`
`wifi ap` ลืม STA ที่บันทึกแล้วเปิด AP `Nomad-SDR` / `nomadsdr1121`
คำตอบไม่ใส่รหัสผ่าน ห้ามตั้งค่าระหว่างสตรีม I/Q

ทางเลือกตอน build: คัดลอก `nomad/src/wifi.example.h` เป็น `nomad/src/wifi.local.h`
แล้วกำหนด `NOMAD_STA_SSID` และ `NOMAD_STA_PASSWORD` ใช้เมื่อยังไม่เคยบันทึกผ่าน UART
ไฟล์ local ถูก Git ignore และไม่ควรใส่รหัสผ่านใน source ที่ติดตามด้วย Git
อิมเมจที่ build แล้วมี credentials รวมอยู่ด้วย จึงเก็บใน `dist/` ที่ถูก ignore

เมื่อมี SSID จะเริ่มแบบ STA, รับ IP จาก DHCP และ reconnect อัตโนมัติ
หากเชื่อมไม่ได้ภายใน 20 วินาที จะเปิด AP `Nomad-SDR` เพิ่มเป็นทางสำรอง
USB ใช้ได้ระหว่างรอเชื่อมต่อ และไม่มีข้อความ Wi-Fi แทรกระหว่าง JSON/IQ stream
หากไม่มีไฟล์ local, NVS ว่าง และ SSID ว่าง จะใช้ AP ตามเดิม

ตรวจ IP และสถานะโดยไม่แสดงรหัสผ่าน:

```powershell
python host/bridge.py --port COM3 --radio 0 wifi
```

ใช้ค่า `ip` ที่ได้แทน `NOMAD_IP` โดย PC ต้องเข้าถึงเครือข่ายเดียวกันได้:

```powershell
python host/bridge.py --port socket://NOMAD_IP:1121 probe
python host/bridge.py --port socket://NOMAD_IP:1122 probe
python host/nomad_rx.py --host NOMAD_IP --radio 0 --frequency 915000000 --seconds 2 --output lan-radio0.cf32
```

คำสั่ง `<id> wifi` ใช้ได้ทั้ง UART และ TCP สำหรับดูสถานะ: mode, SSID, connection,
IP/gateway/subnet/RSSI และสถานะ AP เท่านั้น DHCP อาจเปลี่ยน IP หลังรีบูต
`<id> wifi sta ...` และ `<id> wifi ap` ใช้ได้เฉพาะ UART

STA ที่บันทึกผ่าน UART อยู่ใน NVS; IP ได้จาก DHCP ดูด้วยคำสั่ง `wifi`
USB native ดู [docs/usb-native.md](usb-native.md)

การวัด TCP ล้วนใน session นี้ส่ง 367,616 bytes ใช้เวลาฝั่งรับประมาณ 1.245 s
(ประมาณ 295 kB/s) ขณะที่ LIQ1 ที่ 62.5 kS/s ต้องส่ง 397 kB/s ต่อชิป
การทดสอบ capture ต่อเนื่องจึงพบ queue-full (`flags=2`); host เก็บ partial capture
พร้อม `complete=false` ตามเดิม การเชื่อมต่อ STA สำเร็จไม่ได้แปลว่า throughput
ของเครือข่ายนี้พอสำหรับ long capture ในรูปแบบปัจจุบัน
ผลการทดสอบแยกอยู่ที่ `build/nomad-sta-validation.json`
TCP sender รวมข้อมูลเป็นชุดตาม TCP MSS และ LIQ1 decoder ยังตรวจ CRC ทีละเฟรม

### เข้าถึง main ESP32

ต้องเข้าถึง UART/download mode ของ **main ESP32**
USB/COM ที่แสดง ESP32-C3 เป็น backpack จึงใช้แฟลช image นี้โดยตรงไม่ได้
อย่าใช้การระบุ `esp32dev` เป็นหลักฐานว่า USB ของ Nomad ต่อ main MCU
ตรวจ schematic/PCB revision และใช้ UART 3.3 V, GND ร่วม, boot strap/reset ที่ถูกต้อง
repo นี้ไม่มีข้อมูลตำแหน่ง test pad ที่ยืนยันแล้ว จึงไม่ได้เดาจุดต่อสาย

เครื่องที่ทดสอบใน session นี้ต่อ USB ปกติเป็น **COM3 / CP210x** และ esptool
ตรวจพบ **ESP32-PICO-D4 revision 1.1, flash 4 MB** จึงเข้าถึง main MCU ได้โดยตรง
ใช้ผลตรวจชิปจริงตัดสิน ไม่สรุปจากชื่อ USB bridge เพียงอย่างเดียว
สำรองแฟลชก่อนติดตั้งที่ `build/backups/nomad-com3-main-bootloader-backup.bin`
พร้อม SHA256/partition table ใน `build/backups/nomad-backup.json`
ตรวจเทียบกับชิปขณะค้าง bootloader แล้วผ่าน (`verify_flash: digest matched`)

ตัวอย่างเมื่อได้ `COM_MAIN` และเข้า download mode ของ main ESP32 แล้ว
(แทนด้วย COM จริง; ใช้ esptool จาก `pio pkg exec` ในโฟลเดอร์ `nomad`):

```powershell
cd nomad
python -m platformio pkg exec -p tool-esptoolpy -- esptool.py --chip esp32 --port COM_MAIN flash_id
python -m platformio pkg exec -p tool-esptoolpy -- esptool.py --chip esp32 --port COM_MAIN read_flash 0 0x400000 ../nomad-main-backup.bin
python -m platformio pkg exec -p tool-esptoolpy -- esptool.py --chip esp32 --port COM_MAIN write_flash 0x0 ../dist/nomad/nomad-sdr-merged.bin
cd ..
```

ขนาด backup ต้องตรงกับผล `flash_id`; ตัวอย่างนี้ใช้ 4 MB
merged image เปลี่ยน layout/แอป ELRS ของ main ESP32 จึงควรเก็บ full-flash backup
และ hardware/config ของ ELRS เดิมก่อน แฟลชนี้ไม่มี LR1121 firmware รวมอยู่
คืน main ESP32 ได้ด้วย full backup ที่ offset 0 หรือเฟิร์มแวร์ ELRS Nomad ตามวิธีกู้คืนของผู้ผลิต

### ตรวจ LR1121 และเตรียม firmware 1.3

ผ่าน USB โดยไม่ต้องมี Wi-Fi adapter บน PC (เฟิร์มแวร์ Nomad 0.2.0 ขึ้นไป):

```powershell
python host/bridge.py --port COM3 --radio 0 probe
python host/bridge.py --port COM3 --radio 1 probe
python lr1121/install.py stock --port COM3 --radio 0 --out build/nomad-radio0
python lr1121/install.py stock --port COM3 --radio 1 --out build/nomad-radio1
```

อย่าใช้ UART กับ TCP ควบคุมชิปเดียวกันพร้อมกัน
UART เลือกชิปด้วยคำสั่ง `<id> radio 0` / `<id> radio 1`; host ทำให้อัตโนมัติเมื่อมี `--radio`

หลังบูตพอร์ตและต่อ Wi-Fi `Nomad-SDR`:

```powershell
python host/bridge.py --port socket://192.168.4.1:1121 probe
python host/bridge.py --port socket://192.168.4.1:1122 probe
```

ตรวจ `versions[].data`; ELRS บางรุ่นใช้ firmware type `f3` / รุ่นอื่น ซึ่งใช้ RAM layout
ของโปรเจกต์ SDR นี้ไม่ได้ ตัวรับจะหยุดก่อนเขียน RAM และ **ไม่เปลี่ยน LR firmware อัตโนมัติ**

หากต้องเปลี่ยนเป็น stock 1.3 ให้ใช้ application-only installer เดิมทีละชิป:

```powershell
git submodule update --init external/radio-firmware-images
python lr1121/install.py stock --port socket://192.168.4.1:1121 --out build/nomad-radio0
python lr1121/install.py stock --port socket://192.168.4.1:1122 --out build/nomad-radio1
```

คำสั่ง `stock` ลบ/เขียน application ของชิปที่ระบุ โดยตรวจ vendor SHA256 และ bootloader
identity; คง bootloader เดิม ไม่ใช่การสำรอง application ของ ELRS
ควรเตรียมวิธีลง LR firmware ที่ ELRS รุ่นเดิมต้องการไว้ด้วย
installer รองรับต้นทาง `22f30104` ที่อ่านพบจริง โดยตรวจ bootloader `22df2100` ก่อนลบ
เก็บอิมเมจ ELRS F30104 ที่แปลงจาก header ของ Semtech/ELRS ตาม revision ที่อ้างไว้
พร้อม license ใน `build/backups/lr1121-elrs-f30104.*` แล้ว คำสั่งกู้คืนเฉพาะ LR1121:

```powershell
python lr1121/install.py restore-elrs --port COM3 --radio 0 --out build/restore-radio0
python lr1121/install.py restore-elrs --port COM3 --radio 1 --out build/restore-radio1
```

คำสั่งกู้คืนตรวจ SHA256 และขนาดของอิมเมจ ELRS ที่ pin ไว้ก่อนเปิดอุปกรณ์
จากนั้นคืน main ESP32 ด้วย full backup หากต้องการกลับไปใช้ ExpressLRS เดิม
ห้ามเปิด capture/probe จาก client อื่นพร้อม provisioning
ไม่ใช้ `forge/install/verify` ของ ARC extension กับพอร์ตนี้; ไม่ใช้ `rf-init/rx-start` ของ
Waveshare helper กับ Nomad (มีการตรวจปฏิเสธก่อนเขียนค่า)

## Capture

ทดสอบ burst ผ่าน USB (ตัวอย่าง 16 blocks / 2,000 complex samples):

```powershell
python host/nomad_rx.py --port COM3 --radio 0 --frequency 915000000 --rate 62500 --seconds 0.032 --output usb-radio0.cf32
python host/nomad_rx.py --port COM3 --radio 1 --frequency 2440000000 --rate 62500 --seconds 0.032 --output usb-radio1.cf32
```

UART ไม่รองรับ `--radio both` และไม่รองรับ continuous capture
ปิด socket จะ reset ชิปอัตโนมัติ แต่การปิด UART ไม่มีการ reset อัตโนมัติ;
ใช้ `bridge.py --port COM3 --radio N reset` เมื่อต้องการ reset

เริ่มจากสองวินาทีที่ 62.5 kS/s:

```powershell
python host/nomad_rx.py --radio 0 --frequency 915000000 --rate 62500 --seconds 2 --output radio0.cf32
python host/nomad_rx.py --radio 1 --frequency 2440000000 --rate 62500 --seconds 2 --output radio1.cf32
python host/nomad_rx.py --radio both --frequency 915000000 --frequency2 2440000000 --rate 62500 --seconds 2 --output dual.cf32
```

โหมด `both` ให้ `dual.radio0.cf32` / `dual.radio1.cf32` และ JSON แยกกัน
หนึ่งช่องลอง `--rate 125000` ได้ แต่ throughput ยังไม่ผ่านการวัดจริง
เปิดจูน 150–2500 MHz ตามช่วง synthesizer ของ LR1121 โดยแบ่งช่วงที่ผู้ผลิต
มี RX specifications กับช่วงคั่นกลางที่เป็นการทดลอง ดูรายละเอียดในคู่มือ live SDR
ช่วงนี้ไม่ใช่ผลรับรอง sensitivity/bandwidth ของ Nomad และไม่รวม FM 88–108 MHz
หนึ่ง capture จำกัด 8192 blocks × 125 samples (16.384 s ที่ 62.5 kS/s)
Wi-Fi ของ ESP32 ส่งในย่าน 2.4 GHz จึงอาจรบกวนการวัดย่านเดียวกัน

ไฟล์ `*.cf32.json` ต้องเป็น `complete: true`, `stats.flags: 0`,
`lost_samples: 0`, produced/sent/requested_blocks เท่ากัน
หากผิดพลาด โปรแกรม exit nonzero และเก็บ partial file พร้อม `complete: false`
ไม่เขียนทับไฟล์เดิม การปิด socket ทำให้เฟิร์มแวร์หยุดและ reset เฉพาะชิปนั้น

## ขอบเขตการทดสอบ

ผลบน Nomad จริงวันที่ 2026-11-04 ผ่าน COM3 / CP210x:

| ชิป | ความถี่ | sample rate | complex samples | CRC/sequence/loss |
| --- | --- | --- | --- | --- |
| 0 | 915 MHz | 62.5 kS/s | 2,000 | ผ่าน / flags=0 / lost=0 |
| 0 | 915 MHz | 125 kS/s | 2,000 | ผ่าน / flags=0 / lost=0 |
| 1 | 2440 MHz | 62.5 kS/s | 2,000 | ผ่าน / flags=0 / lost=0 |
| 1 | 2440 MHz | 125 kS/s | 2,000 | ผ่าน / flags=0 / lost=0 |

ทั้งสองชิปอ่าน version `22030103` คงที่และ error flags `0x0000`
bootloader ก่อน/หลัง provisioning เป็น `22df2100` เหมือนเดิม
ไฟล์ผลรวมอยู่ที่ `build/nomad-hardware-validation.json`; capture และ metadata ใน
`build/nomad-radio0/` / `build/nomad-radio1/`
ตัวเลขนี้เป็นการอ่าน I/Q burst ระยะสั้นผ่าน UART ไม่ได้ป้อน RF tone อ้างอิง
และยังไม่ได้ทดสอบ Wi-Fi streaming หรือการรับสองช่องพร้อมกัน

ตรวจ offline: firmware build, shared C parser/LIQ1 codec, Python regression tests,
TCP loopback จริงบน Windows, fragmented JSON ต่อด้วย binary, CRC, sample sign/scale,
sequence/terminal count, firmware mismatch, DMA layout mismatch และ profile ของ Nomad

ยังต้องทำบน Nomad จริง: วัดสัญญาณ RF switch และ capture tone ที่ทราบความถี่
ทีละช่องแล้วสองช่อง, วัด phase continuity/อัตราขาดหาย,
ทดสอบตัด Wi-Fi/คิวเต็ม/กลับมาเชื่อมต่อ, และ long-run ที่แต่ละ rate
CRC/sequence ถูกต้องเพียงอย่างเดียวไม่ยืนยันว่า ADC ไม่เคยเสีย I/Q pair
