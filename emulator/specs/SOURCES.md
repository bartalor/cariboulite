# Hardware specification sources

This directory holds machine-readable register descriptions for the hardware
emulated by the CaribouLite QEMU model. Each spec is derived from a vendor
datasheet, pinned below by URL and content hash so the derivation is
reproducible.

The datasheet PDFs are **not** vendored into this repository (they are
copyrighted vendor documents). Fetch them with `curl` and verify the
`sha256` before editing any spec file.

## Format and tooling

Specs are authored in **SystemRDL 2.0**, the Accellera-blessed register
description language. The rationale for choosing SystemRDL over alternatives
(hand-written SVD, IP-XACT, HJSON, etc.) is summarised in the DVCon paper
*"Comprehensive Register Description Languages"* (Black & Smith, Doulos),
which identifies SystemRDL as the closest available standard for CSR
authoring. There is no single dominant industry standard; SystemRDL is the
strongest citable candidate and has a real, actively maintained open
toolchain.

The toolchain:

- `systemrdl-compiler` (MIT) — SystemRDL 2.0 front-end.
- `peakrdl` (LGPL-3.0) — multi-target code generator built on top of
  `systemrdl-compiler`. Provides `peakrdl c-header`, `peakrdl html`,
  `peakrdl regblock`, `peakrdl uvm`, `peakrdl ip-xact`, etc.
- [`rdl2qemu.py`](rdl2qemu.py) — this repo's small QEMU-flavoured exporter.
  Emits a header using QEMU's in-tree `hw/core/registerfields.h` idiom
  (`REG8` / `FIELD`), which is what upstream QEMU device models and their
  qtest conformance tests consume.

The generated header is the single source of truth for register offsets,
reset values, and enumerated field values used by both the QEMU device
model and its qtest. Hand-editing the header is forbidden; regenerate it
from the `.rdl` instead.

### Regenerate

```sh
python3 -m venv .venv
.venv/bin/pip install 'peakrdl>=1.5,<2'
.venv/bin/python3 specs/rdl2qemu.py \
    specs/at86rf215.rdl \
    ../../../qemu/include/hw/ssi/at86rf215_regs.h
```

## AT86RF215

- Vendor: Microchip (formerly Atmel)
- Document: `Atmel-42415E-WIRELESS-RF215_Datasheet`, revision 05/2016
- URL: <https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-42415-WIRELESS-AT86RF215_Datasheet.pdf>
- sha256: `4b61a09d20ed2411ad333f6a02012eb1f42642d0bdd39dc9636fa6f7cadf688b`
- Size: 10657452 bytes (235 pages)

Spec file: [`at86rf215.rdl`](at86rf215.rdl)

Note: Microchip does **not** publish a CMSIS-Pack or ATDF for the
AT86RF215 (their packs repository at <https://packs.download.microchip.com/>
only covers MCU families — ATmega, ATtiny, SAM, PIC, etc.). The ASF C
header `at86rf215.h` exists but ships under a restricted "use exclusively
with Microchip products" licence and cannot be redistributed in a
GPL-licensed repo. The `.rdl` in this directory is hand-authored from the
datasheet PDF, with every numeric value accompanied by an exact datasheet
citation in a `//` comment; this is the only path available for this chip.

### Register coverage

| Register | Offset | Datasheet section | Status |
|----------|--------|-------------------|--------|
| `RF_PN`  | 0x000D | §1.1.3.1          | specced |

All other registers are currently unimplemented in the QEMU model.
