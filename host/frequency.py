# SPDX-License-Identifier: MIT
"""LR1121 synthesizer bounds, distinct from characterized RF receiver bands.

Semtech LR1121 datasheet Rev 2.0: tables 3-7, 3-8 and 3-9.
https://www.hy-line-group.com/products/hcp/datasheet/semtech/lr1121-datasheet.pdf
"""
MIN_FREQUENCY = 150_000_000
MAX_FREQUENCY = 2_500_000_000


def valid_frequency(value):
    return type(value) is int and MIN_FREQUENCY <= value <= MAX_FREQUENCY


def receiver_band(value):
    for low, high, label in ((150_000_000, 960_000_000, 'sub_ghz'),
                             (1_900_000_000, 2_200_000_000, 's_band'),
                             (2_400_000_000, 2_500_000_000, '2g4')):
        if low <= value <= high:
            return label
    return 'experimental_synth_range'
