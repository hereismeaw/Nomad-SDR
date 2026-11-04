/* SPDX-License-Identifier: MIT */
#pragma once
#include <stdint.h>

// ExpressLRS/targets, TX/Radiomaster Nomad.json (see docs/nomad.md).
namespace board {
constexpr int sck = 25, miso = 33, mosi = 32;
constexpr int cs[2] = {27, 13}, busy[2] = {36, 39};
constexpr int reset[2] = {15, 21}, dio9[2] = {37, 34};
constexpr int pa_apc = 26, fan = 2, backpack_en = 19, led = 22;
constexpr unsigned led_count = 2;
constexpr uint16_t port[2] = {1121, 1122};
constexpr uint32_t stream_spi = 16000000;
constexpr uint32_t uart_baud = 921600;
constexpr unsigned queue_frames = 48;
}

