# LR1121: สิ่งที่พัฒนาต่อบน Nomad ได้จาก Lora-net

ตรวจเมื่อ 2026-11-05 จาก source และเอกสารของ Semtech โดยตรง
เอกสารนี้เป็นผลสำรวจและข้อเสนอ ฟีเจอร์ส่วนใหญ่ยังต้องพัฒนา
หลังการสำรวจได้ทดลอง CBC/ARC extension บนชิป 1 สำเร็จ รวม known-vector packing
และ RF snapshot ที่ 915/2440 MHz ดู [ผลทดลองและสถานะบอร์ด](nomad-extension-experiment.md)
รุ่น 0.11.0 เพิ่ม [control API](control-api.md) สำหรับ sweep, LoRa/GFSK monitor,
CAD, gain, diagnostics และ dual jobs แล้ว ผลด้าน sensitivity และ RF packet
ยังต้องวัดด้วยเครื่องส่งอ้างอิง

## ข้อสรุปสำหรับ Nomad-SDR

งานที่เหมาะทำก่อนคือ **RSSI sweep และ LoRa/GFSK packet monitor**
เพราะส่งข้อมูลน้อยกว่า I/Q มาก และนำ LR1121 สองตัวมาแบ่งหน้าที่ได้
ส่วนการเพิ่ม bandwidth ของ SDR ต้องปรับการเก็บ/แพ็กข้อมูลภายในวิทยุและเส้นทาง SPI
การเพิ่ม sample rate ใน SDRangel อย่างเดียวไม่ช่วย

| แนวทาง | หลักฐานใน repo | สิ่งที่ต้องทำบน Nomad | สถานะ |
| --- | --- | --- | --- |
| Spectrum / RSSI sweep | SWSD003 มี spectral_scan และ spectrum_display | จูนทีละช่อง อ่าน RSSI หลายครั้ง เก็บ min/mean/max/histogram ส่ง CSV/JSON | มีตัวอย่างทางการ พร้อมนำมาพอร์ต |
| LoRa/GFSK packet monitor | SWDR001 มี RX, packet status, CRC, IRQ และ CAD | เพิ่ม packet mode แยกจาก SDR, ตั้ง frequency/SF/BW/syncword, บันทึก payload/RSSI/SNR | ใช้ API ปกติ ไม่ต้องลง ARC extension |
| CAD activity detector | SWSD003 มีตัวอย่าง cad | ตรวจ activity ของ LoRa ตามพารามิเตอร์ที่ตั้ง แล้วสั่งเริ่มจับ packet | ต้องทดสอบการตรวจพบ/พลาดกับเครื่องส่งอ้างอิง |
| RxBoosted / LNA profiles | SWDR001 มี API และ helper สำหรับ LF0 | เพิ่ม profile ให้ผู้ใช้เลือก แล้ววัด sensitivity และ clipping | API มีจริง ผลกับวงจร Nomad ยังไม่วัด |
| RF die temperature / supply diagnostics | SWDR001 มี GetTemp/GetVbat | แสดงค่าแยก LR1121 ทั้งสองตัว และทดลองประกอบการควบคุมพัดลม | ต้องตรวจจังหวะอ่านที่ไม่รบกวน I/Q |
| LoRaWAN modem / relay | Modem-E มี stack และ direct radio access | เป็น firmware profile อีกแบบ พร้อม HAL/BSP ของ Nomad | ยังไม่รองรับใน SDR ปัจจุบัน |
| แพ็ก I/Q / decimate ใน LR1121 | สายงาน ARC/FIFO1 อยู่ใน repo ต้นทางของ SDR นี้ | ทดสอบ throughput ที่สูงขึ้นและ dual mode ต่อ | packed USB ต่อเนื่องผ่านแล้วใน 0.10.0; ยังไม่ได้ทำ decimation ใน LR1121 |

ตัวอย่างสแกนทางการใช้การวัด RSSI ทีละความถี่ ไม่ใช่ FFT พร้อมกันทั้งย่าน
จึงทำภาพ spectrum กว้างกว่าหน้าต่าง I/Q ได้ แต่มีเวลาสแกนและอาจพลาดสัญญาณสั้น
RSSI และความไวต้องสอบเทียบกับ RF matching/เสาอากาศจริงของ Nomad

แหล่งอ้างอิง:

- [Spectral scan](https://github.com/Lora-net/SWSD003/blob/08912a2324bfc931224d368984b58b4a853078ad/lr11xx/apps/spectral_scan/README.md)
- [Spectrum display](https://github.com/Lora-net/SWSD003/blob/08912a2324bfc931224d368984b58b4a853078ad/lr11xx/apps/spectrum_display/README.md)
- [Radio API](https://github.com/Lora-net/SWDR001/blob/a333238acfa0a9dee9ce2824ce52e89b98f3d24b/src/lr11xx_radio.h)
- [System API](https://github.com/Lora-net/SWDR001/blob/a333238acfa0a9dee9ce2824ce52e89b98f3d24b/src/lr11xx_system.h)

## ใช้สองชิปให้คุ้ม

ข้อเสนอนี้อนุมานจาก API และฮาร์ดแวร์สองวิทยุ ยังไม่ใช่ผลทดสอบ:

- แบ่งความถี่สแกนให้คนละครึ่ง ลดจำนวนช่องที่แต่ละชิปต้องจูน
- ชิปหนึ่งสแกน อีกชิปจับ packet หรือ I/Q ณ ช่องที่สนใจ
- จับ LoRa/GFSK สองช่องพร้อมกัน ลด bandwidth ที่ต้องส่งเทียบกับ dual I/Q
- เปรียบเทียบ RSSI/packet จากสองเสาอากาศเพื่อทดลอง diversity

ELRS/FHSS sniffer ต้องเพิ่มการตาม channel hopping, timing และพารามิเตอร์ PHY
การมี LoRa receiver สองตัวไม่ได้ทำให้ถอด ELRS ทุกโหมดได้ทันที
การรับ LoRaWAN PHY ได้ก็ไม่ได้แปลว่าถอด plaintext ของ payload ที่เข้ารหัสได้
การรวม I/Q แบบ phase coherent หรือ direction finding ต้องวัด clock/phase และ
ออกแบบ synchronization เพิ่ม ยังไม่มีหลักฐานว่า Nomad-SDR ทำได้

## RxBoosted และ LNA ไม่ใช่ปุ่มเพิ่ม gain แบบไม่จำกัด

API ที่น่าพอร์ตคือ `lr11xx_radio_cfg_rx_boosted` และ `lr11xx_radio_set_lna_mode`
ตัวหลังเลือก topology ของขาเข้า LF0 (single-ended หรือ differential)
จึงต้องตรวจวงจร RF ของ Nomadก่อน ไม่ควรตีความเป็น gain control ทั่วไป
เอกสารกำหนดให้ตั้ง LNA mode หลังเข้า RX จึงต้องวางลำดับคำสั่งให้ถูก
ทดสอบกับสัญญาณอ้างอิงที่ระดับคงที่ก่อนกล่าวอ้างว่าความไวดีขึ้น

[Implementation ทางการ](https://github.com/Lora-net/SWDR001/blob/a333238acfa0a9dee9ce2824ce52e89b98f3d24b/src/lr11xx_radio.c)

## ทางทดลอง firmware และข้อจำกัดที่ยืนยันได้

Changelog ของ LR1121 ระบุว่า 0x0104 เพิ่ม Low latency APIs และแก้ CVE กลุ่มแรก
ส่วน 0x0105 แก้ CVE-2026-6232 เอกสารที่ตรวจยังไม่ยืนยันว่า API ใหม่ให้ raw I/Q
หรือว่า DMA layout เดิมคงเดิม จึงยังสรุปไม่ได้ว่าอัปเกรดแล้ว SDR เร็วขึ้น

Semtech ยืนยันว่ามีช่องทาง SPI ในเฟิร์มแวร์เก่าที่ทำให้รัน firmware/code
ที่ไม่ได้รับรองได้ นี่เป็นหลักฐานว่าการทำ custom DSP/extension บนชิปมีเหตุผล
ให้ศึกษา แต่ไม่ได้เป็นคำยืนยันว่า extension ของเราใช้ได้กับทุกเวอร์ชัน
ยังไม่ได้ทดลองช่องโหว่ใหม่หรือเปลี่ยน bootloader ในงานนี้

- [Transceiver changelog](https://github.com/Lora-net/radio_firmware_images/blob/e1e1a328567bc78018a072fda7d318a7d022899f/lr1121/transceiver/CHANGELOG.md)
- [SEM-PSA-2026-001](https://www.semtech.com/uploads/bulletins/SEM-PSA-2026-001.pdf)
- [SEM-PSA-2026-002](https://www.semtech.com/uploads/bulletins/SEM-PSA-2026-002.pdf)

บอร์ดนี้ใช้ transceiver 0x0103 และโค้ดตรวจ DMA layout ก่อนเขียน ring
ให้คง baseline นี้สำหรับ SDR จนกว่าจะมีแผนทดลองและกู้คืนที่ตรวจสอบได้
ยังไม่มีผล hardware เปรียบเทียบ 0x0103/0x0104/0x0105 บน Nomad เครื่องนี้
การอัปเกรดเป็นรุ่นแก้ช่องโหว่เป็นคนละโจทย์กับการรักษา compatibility ของ SDR

แนวคิดสำหรับเพิ่ม throughput: ย้าย block-floating packing หรือ decimation
จาก ESP32 เข้า LR1121 ก่อนอ่าน SPI เพื่อลดจำนวนไบต์บนบัส
ปัจจุบัน ring เก็บ 8 ไบต์ต่อ complex sample ทำให้ native 62.5 kS/s
ต้องอ่านอย่างน้อย 500000 B/s ต่อชิป ก่อนรวม overhead
SPI 16 MHz ที่ใช้ร่วมกันมีเพดานทางทฤษฎี 2000000 B/s
ดังนั้น 250 kS/s แบบเดิมเพียงชิปเดียวก็เต็มเพดานข้อมูลแล้ว
การทำ FIFO ที่แพ็กข้อมูลก่อนอ่านมีเหตุผล แต่ต้องวัด execution time และ loss จริง

## Modem-E มี direct radio access แต่ยังไม่ใช่ SDR profile ของเรา

README ของ lr1121_modemE_driver ระบุชัดว่ามี transceiver APIs
และเปิดคำสั่งวิทยุเมื่อ suspend modem ได้ ส่วน register/memory commands
เป็นข้อยกเว้นที่ใช้ได้โดยไม่ต้อง suspend ตามรายการในเอกสาร
ดังนั้นข้อสรุปว่า Modem-E ตัดการเข้าถึงวิทยุทั้งหมดไม่ถูกต้อง
สิ่งที่ยังไม่ทราบคือ memory map, callback และ DMA ของ Modem-E จะใช้กับ SDR
ทางปัจจุบันได้หรือไม่ โค้ดเรายังตรวจให้เป็น stock 0x0103 เท่านั้น

[Modem-E driver README](https://github.com/Lora-net/lr1121_modemE_driver/blob/0de05dd6a49da3d3962bf7041071ca8ca185a08a/README.md)

## สิ่งที่ยังปลดล็อกให้เป็น LR1121 feature ไม่ได้จากหลักฐานนี้

- GNSS scanning, Wi-Fi geolocation scanning และ RTToF: driver ระบุ LR1110/LR1120 เท่านั้น
- BLE beacon compatibility: README จำกัด LR1110/LR1120 เช่นกัน
- Wi-Fi ของ ESP32 บน Nomad เป็นอีกชิป ไม่ใช่การเปิด Wi-Fi receiver ใน LR1121
- ตัวอย่าง one_channel_hub ใช้ตระกูล SX126x/LLCC68 เป็นหลัก ไม่ใช่ firmware
  ที่นำมาแฟลช Nomad แล้วได้ LR1121 concentrator ทันที
- ชื่อ BPSK/LR-FHSS ใน enum ไม่เพียงพอที่จะสรุปว่ามี packet RX สำหรับทุก PHY
  ต้องตรวจความสามารถของ LR1121 และทิศทาง RX/TX ก่อนเพิ่มใน feature list
- ยังไม่พบ public API สำหรับ continuous raw I/Q ในไดรเวอร์ที่ตรวจ
  LoRa standard/inverted IQ เป็น polarity ของ modulation ไม่ใช่ raw-I/Q output

[Driver README](https://github.com/Lora-net/SWDR001/blob/a333238acfa0a9dee9ce2824ce52e89b98f3d24b/README.md),
[RTToF demo](https://github.com/Lora-net/lr11xx_ranging_demo),
[One channel hub](https://github.com/Lora-net/one_channel_hub)

## ลำดับงานที่แนะนำ

1. ทำ RSSI sweep แบบ RX-only พร้อมไฟล์ CSV/JSON และ dwell time ที่ผู้ใช้ตั้งได้
2. เพิ่ม LoRa/GFSK packet monitor พร้อม CRC/RSSI/SNR และสถิติ dropped packets
3. เพิ่ม RF diagnostics และทดลอง RxBoosted ด้วย reference signal
4. แบ่งชิป scan/monitor และวัด contention บน SPI ร่วมก่อนเปิด dual mode
5. แยกสาขาทดลอง ARC/FIFO1 เพื่อแพ็ก I/Q ภายใน LR1121 ก่อนย้ายเข้าเฟิร์มแวร์หลัก

สำเนาอ้างอิงสำหรับอ่าน source อยู่ใน ignored `build/semtech-research/`
โดยไม่เพิ่ม dependency ใหม่ให้ firmware production
