# LIQ8 compact receive transport

Nomad firmware 0.4.0 adds `ID stream8 RATE BLOCKS` (RATE 62500/125000,
BLOCKS 0..8192; 0 means indefinite). Stop with ETX byte `03` and drain the terminal
frame before sending ASCII commands. Stock LR1121 transceiver 1.3 is required.
No ARC extension or LR firmware rewrite is required when upgrading from 0.3.0.

The 44-byte header uses the LIQ1 layout from `pico/firmware/stream_format.c`,
with magic `LIQ8`. Header CRC32 covers bytes 0..39 after replacing the magic.
Data frames have 125 complex samples and payload length 251:

| Offset in payload | Contents |
| --- | --- |
| 0 | unsigned shared shift, 0..16 |
| 1..250 | signed two's-complement int8 I,Q components, interleaved |

Decoded normalized float component = `signed_byte * 2**(shift-22)`.
The encoder chooses a per-block power-of-two scale from the maximum magnitude
of the validated signed-23 input. Rounding is nearest, ties away from zero;
component error is at most half a scaled quantization step. This representation
preserves the scale per block but reduces component precision. It is not lossless.

The original signed-23 acquisition and DMA ownership checks remain unchanged.
Packing, CRC and network framing happen in the consumer task. TCP writes may
contain multiple frames or parts of frames; clients must read by header lengths.

Terminal frames use type 2, payload 36 bytes and the original nine counters/flags.
Sequence counts 125-sample banks; sample index is `sequence*125 mod 2**32`.
ETX termination flag 4 is expected for an explicitly cancelled stream. Queue-full
flag 2 is a capture failure. Both header/payload CRCs and continuity must be checked.

62500 S/s requires 147500 B/s per radio including data headers; 125000 S/s
requires 295000 B/s. The host rtl_tcp bridge uses 62500 S/s natively and FIR
interpolation for the application's requested 62500/125000/250000 S/s rate.
