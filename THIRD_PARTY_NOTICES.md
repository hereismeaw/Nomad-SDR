# Third-party notices

Independent project code and documentation use MIT (see `LICENSE`). All project
code, patches and tests under `sdrpp/` use GPL-3.0-only (see `sdrpp/LICENSE`).
`host/nomad_rx.py` and `host/tests/test_nomad.py` also use GPL-3.0-only;
`host/nomad_rtl_tcp.py` and `host/tests/test_rtl_tcp.py` use the same license.
the receiver setup and decoding are adapted from the SDR++ device implementation.
[License scope](docs/licensing.md) lists the directory boundaries. Copies of
upstream components retain their own notices and terms; neither project license
relicenses them.

- **SDR++**, Alexandre Rouma and contributors: GPL-3.0. Pinned source and license
  in `external/sdrplusplus`. The module and core patch build against that revision.
- **Raspberry Pi Pico SDK / picotool**: BSD-3-Clause and included component
  licenses, preserved in their respective submodules. Pico SDK's nested TinyUSB
  source has its own MIT license and notices.
- **GNU binutils**: GPL and other component licenses in `external/binutils`.
  Only the build tools are used; no tool binaries are checked into this repository.
- **Semtech LR1121 firmware**: the terms beside the 0x0103 image in
  `external/radio-firmware-images/lr1121/transceiver/` apply to that binary and
  its redistribution. It is not covered by either project license grant.
- **radioegor146/lr-semtech-research**: MIT, copyright 2026 radioegor146.
  The CBC-oracle image construction in `lr1121/install.py` is adapted from that
  research. The complete notice is retained at
  `tools/third-party-licenses/radioegor146-MIT.txt`.
  Reference revision: `ed178ae8567e3525ebd5b1c698590b6de4900405`.
- **Waveshare Core1121-XF demo**: board setup constants informed the TCXO and RF
  switch configuration; the demo is not bundled or a build dependency.
- **ExpressLRS Targets / LR1121 driver**: Nomad pin assignments and the default
  RF-switch table are hardware configuration facts referenced by `nomad/src/board.h`
  and `host/nomad_rx.py`; links and inspected revision are recorded in `docs/nomad.md`.
- **Espressif Arduino ESP32**: LGPL-2.1-or-later with separately licensed bundled
  components; PlatformIO downloads this framework for the Nomad build. Its original
  notices and source remain in the installed package and upstream repository.

The macOS bundler includes both project licenses, this notice, the license-scope
document, the upstream SDR++ license and notices for the dynamically
linked FFTW, VOLK, GLFW, PortAudio, ORC, cpu_features and zstd libraries from
`tools/third-party-licenses/`. Those libraries are supplied by the host package
manager, not source-pinned here. Anyone distributing a binary must also meet the
corresponding source and notice requirements for the exact libraries they ship;
including these notice files alone is not a substitute for those obligations.

Research links: [radioegor146](https://github.com/radioegor146/lr-semtech-research),
[LakeShark](https://github.com/SAMS0N1TE/LakeShark),
[LR2021 SDR](https://github.com/SAMS0N1TE/lr2021-sdr),
[Semtech firmware images](https://github.com/Lora-net/radio_firmware_images),
[Waveshare Core1121-XF](https://www.waveshare.com/wiki/Core1121-XF).
