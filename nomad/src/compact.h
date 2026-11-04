/* SPDX-License-Identifier: MIT */
#pragma once
#include <stdbool.h>
#include <stdint.h>
#define COMPACT_PAYLOAD_BYTES 251u
#ifdef __cplusplus
extern "C" {
#endif
/* 125 complex signed-23 samples -> shift byte + 250 signed-8 components. */
bool nomad_pack8(uint8_t *dst, const uint8_t *src);
typedef struct {
    int32_t i[33], q[33];
    unsigned position, phase;
} nomad_decimator_t;
/* Stateful anti-alias FIR /2. Returns 63 or 62 complex samples, 0 on error. */
unsigned nomad_decimate8(uint8_t *dst, const uint8_t *src, nomad_decimator_t *state);
#ifdef __cplusplus
}
#endif
