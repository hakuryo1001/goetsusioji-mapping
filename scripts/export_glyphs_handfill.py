#!/usr/bin/env python3
"""Export data/glyphs-handfill.json — all PUA glyphs for manual romanization."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONT_CANDIDATES = [
    ROOT / "goetsusioji.ttf",
    ROOT.parent / "goetsusioji-reference" / "goetsusioji.ttf",
]
OUT_PATH = ROOT / "data" / "glyphs-handfill.json"
PUA_START = 0xF021
PUA_END = 0xF545


def find_font() -> Path:
    for path in FONT_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("goetsusioji.ttf not found")


def export() -> dict:
    font_path = find_font()
    font = TTFont(font_path)
    cmap = font.getBestCmap()

    glyphs: dict[str, dict] = {}
    for cp in range(PUA_START, PUA_END + 1):
        if cp not in cmap:
            continue
        glyphs[f"U+{cp:04X}"] = {
            "char": chr(cp),
            "romanization": "",
        }

    total = PUA_END - PUA_START + 1
    return {
        "meta": {
            "font": font_path.name,
            "pua_range": f"U+{PUA_START:04X}..U+{PUA_END:04X}",
            "total_range_slots": total,
            "glyphs_in_font": len(glyphs),
            "empty_slots_in_range": total - len(glyphs),
            "instructions": (
                "Fill romanization for each entry. "
                "Keys are codepoints; char is the glyph (use Goetsusioji font in your editor)."
            ),
        },
        "glyphs": glyphs,
    }


def main() -> int:
    data = export()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUT_PATH} ({data['meta']['glyphs_in_font']} glyphs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
