#!/usr/bin/env python3
"""
Emit a QEMU-idiomatic C header from a SystemRDL register description.

The generated header is the single source of truth for register offsets,
reset values, and enumerated field values used by both a QEMU device
model and its conformance tests. Hand-editing the header is forbidden;
regenerate it from the .rdl file instead.

Usage:
    rdl2qemu.py INPUT.rdl OUTPUT.h [--top NAME]

The output uses QEMU's in-tree register macros (hw/registerfields.h),
which is the idiom upstream reviewers expect:

    REG8(RF_PN, 0x000D)
        FIELD(RF_PN, PN, 0, 8)
    #define RF_PN_RESET 0x34
    #define RF_PN_PN_AT86RF215 0x34
    ...

SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from systemrdl import RDLCompiler
from systemrdl.node import AddrmapNode, RegNode


REG_SIZE_MACRO = {1: "REG8", 2: "REG16", 4: "REG32", 8: "REG64"}


def emit(rdl_path: Path, out_path: Path, top_name: str | None) -> None:
    rdlc = RDLCompiler()
    rdlc.compile_file(str(rdl_path))
    root = rdlc.elaborate(top_def_name=top_name) if top_name else rdlc.elaborate()

    top = None
    for node in root.descendants(unroll=True):
        if isinstance(node, AddrmapNode):
            top = node
            break
    if top is None:
        raise SystemExit("no addrmap found in RDL input")

    device_name = top.inst_name.upper()
    guard = f"HW_SSI_{device_name}_REGS_H"
    lines: list[str] = []
    a = lines.append

    a("/*")
    a(f" * Auto-generated from {rdl_path.name} -- DO NOT EDIT.")
    a(f" * Regenerate with: {Path(__file__).name} {rdl_path.name} {out_path.name}")
    a(" *")
    a(f" * Device: {top.get_property('name') or top.inst_name}")
    desc = top.get_property("desc")
    if desc:
        a(f" * Description: {desc}")
    a(" *")
    a(" * SPDX-License-Identifier: GPL-2.0-or-later")
    a(" */")
    a(f"#ifndef {guard}")
    a(f"#define {guard}")
    a("")
    a('#include "hw/core/registerfields.h"')
    a("")

    for reg in top.descendants(unroll=True):
        if not isinstance(reg, RegNode):
            continue

        size_bytes = reg.size
        macro = REG_SIZE_MACRO.get(size_bytes)
        if macro is None:
            raise SystemExit(
                f"unsupported register size {size_bytes} bytes for {reg.inst_name}"
            )
        size_bits = size_bytes * 8

        reg_name = reg.inst_name
        reg_desc = reg.get_property("desc")
        if reg_desc:
            a(f"/* {reg_desc} */")
        a(f"{macro}({reg_name}, 0x{reg.raw_absolute_address:04X})")

        reset_accum = 0
        has_any_reset = False
        for f in reg.fields():
            a(f"    FIELD({reg_name}, {f.inst_name}, {f.low}, {f.width})")
            f_reset = f.get_property("reset")
            if f_reset is not None:
                has_any_reset = True
                reset_accum |= (int(f_reset) & ((1 << f.width) - 1)) << f.low

        if has_any_reset:
            width_chars = max(2, size_bits // 4)
            a(f"#define {reg_name}_RESET 0x{reset_accum:0{width_chars}X}")

        for f in reg.fields():
            enc = f.get_property("encode")
            if enc is None:
                continue
            width_chars = max(2, f.width // 4) or 2
            for member in enc:
                a(
                    f"#define {reg_name}_{f.inst_name}_{member.name} "
                    f"0x{member.value:0{width_chars}X}"
                )

        a("")

    a(f"#endif /* {guard} */")
    out_path.write_text("\n".join(lines) + "\n")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rdl", type=Path, help="input .rdl file")
    ap.add_argument("header", type=Path, help="output .h file")
    ap.add_argument("--top", default=None, help="top-level addrmap name")
    ns = ap.parse_args(argv)
    emit(ns.rdl, ns.header, ns.top)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
