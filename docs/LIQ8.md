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
Packing happens in the acquisition task; CRC and framing happen in the consumer task. TCP writes may
contain multiple frames or parts of frames; clients must read by header lengths.

Terminal frames use type 2, payload 36 bytes and the original nine counters/flags.
Sequence counts 125-sample banks; sample index is `sequence*125 mod 2**32`.
ETX termination flag 4 is expected for an explicitly cancelled stream. Queue-full
flag 2 is a capture failure. Both header/payload CRCs and continuity must be checked.

62500 S/s requires 147500 B/s per radio including data headers; 125000 S/s
requires 295000 B/s. Default live streaming uses LID8 below, with PC FIR
interpolation for the application's requested 62500/125000/250000 S/s rate.

## LID8 decimated stream

`streamd 62500 BLOCKS` enables a stateful 33-tap anti-alias FIR followed by /2
decimation, then the same block-floating int8 encoding. `BLOCKS` still counts
native 125-sample banks; zero requests an indefinite stream.

The header keeps the LIQ8 layout and CRC rules but uses magic `LID8` and
sample rate 31250. Even sequence numbers carry 63 complex samples (127-byte
payload); odd sequence numbers carry 62 (125-byte payload). Sample index is
`ceil(sequence*125/2) mod 2**32`, including terminal frames. Data frames are
171 and 169 bytes respectively, requiring 85000 B/s at 500 banks per second.
This fits the 921600-baud USB UART, whose 8N1 theoretical limit is 92160 B/s.

Terminal layout and counters are unchanged: produced/sent count native banks,
not output samples. The sample count after N banks is `ceil(N*125/2)`.
The 31.25 kS/s stream has a 31.25 kHz Nyquist span with filter roll-off near
the edges; PC interpolation to 250 kS/s does not widen received RF bandwidth.
