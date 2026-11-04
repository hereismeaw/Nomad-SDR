/* SPDX-License-Identifier: MIT */
#pragma once
#include <Arduino.h>
#include <stdint.h>

void indicatorsBegin();
void indicatorsTick(bool radio0Active, bool radio1Active,
                    uint32_t radio0Flags, uint32_t radio1Flags,
                    unsigned radio0Queued, unsigned radio0Capacity,
                    unsigned radio1Queued, unsigned radio1Capacity);
bool indicatorsCommand(const char *line, Print &out, uint32_t id);
