#!/usr/bin/env python3
"""Sanity checks for the Goetsuese mapping."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "mapping" / "goetsuese-mapping.json"


def main() -> int:
    data = json.loads(MAPPING.read_text(encoding="utf-8"))
    syllables = data["syllables"]
    errors: list[str] = []

    def expect(ini: str, fin: str, cp: str) -> None:
        key = f"{ini}+{fin}"
        got = syllables.get(key, {}).get("codepoint")
        if got != cp:
            errors.append(f"{key}: expected {cp}, got {got}")

    # Grid anchors: col 0 = initial-only; cols 1..25 follow header finals U+F021..U+F039
    expect("l", "e", "U+F1A5")
    expect("lh", "e", "U+F185")
    expect("t", "aon", "U+F157")
    expect("ny", "ie", "U+F36D")
    expect("f", "oq", "U+F0A4")
    expect("kh", "aon", "U+F397")

    grammar = data.get("grammar", {}).get("tsy", {})
    if grammar.get("codepoint") != "U+F3CA":
        errors.append(f"grammar tsy: expected U+F3CA, got {grammar.get('codepoint')}")

    if len(data["initials"]) != 39:
        errors.append(f"expected 39 component initials, got {len(data['initials'])}")
    expected_syllables = data["meta"].get("syllable_row_count", 38) * data["meta"].get(
        "grid_final_count", 25
    )
    if data["meta"]["syllable_entries"] != expected_syllables:
        errors.append(
            f"expected {expected_syllables} syllables, got {data['meta']['syllable_entries']}"
        )
    if data["meta"].get("romanization_entries", 0) < expected_syllables:
        errors.append(
            f"expected at least {expected_syllables} romanization entries, "
            f"got {data['meta'].get('romanization_entries')}"
        )

    # Reference RTF sample decode (F021-grid layout)
    rtf_cps = ["U+F185", "U+F0A4", "U+F397"]
    for cp in rtf_cps:
        match = [k for k, v in syllables.items() if v["codepoint"] == cp]
        if not match:
            errors.append(f"RTF codepoint {cp} not in syllable table")

    if errors:
        print("Validation FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("Validation OK")
    print(f"  {data['meta']['syllable_entries']} syllables, {len(data['initials'])} components")
    print(f"  RTF sample: {' | '.join(f'{cp}={next(k for k,v in syllables.items() if v['codepoint']==cp)}' for cp in rtf_cps)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
