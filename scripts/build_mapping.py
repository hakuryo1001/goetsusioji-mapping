#!/usr/bin/env python3
"""Build Goetsuese romanization → PUA mapping from font grid + chart manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT.parent / "goetsusioji-reference"
FONT_PATH = REF / "goetsusioji.ttf"
MANIFEST_PATH = ROOT / "data" / "chart-manifest.json"
OUT_DIR = ROOT / "mapping"


def load_manifest() -> dict:
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def enumerate_grid(cmap: dict[int, str]) -> tuple[list[int], dict[int, dict[int, int]]]:
    """Return ordered row bases and {row_base: {col: codepoint}}."""
    pua = sorted(cp for cp in cmap if 0xF021 <= cp <= 0xF545)
    rows: list[int] = []
    grid: dict[int, dict[int, int]] = {}
    for cp in pua:
        col = cp & 0x1F
        if col >= 26:
            continue
        row_base = cp & 0xFFE0
        if row_base not in grid:
            grid[row_base] = {}
            rows.append(row_base)
        grid[row_base][col] = cp
    return rows, grid


def cp_str(cp: int) -> str:
    return f"U+{cp:04X}"


def char_str(cp: int) -> str:
    return chr(cp)


def build() -> dict:
    manifest = load_manifest()
    initials = [x["key"] for x in manifest["initials"]]
    finals = [x["key"] for x in manifest["finals"]]

    font = TTFont(FONT_PATH)
    cmap = font.getBestCmap()
    row_bases, grid = enumerate_grid(cmap)

    # Row 0 (U+F020 block): standalone initial component glyphs F021–F03D.
    # These use sequential slots (including col indices 26–29), not the 26-col syllable grid.
    component_initials: dict[str, dict] = {}
    component_cps = [cp for cp in sorted(cmap) if 0xF021 <= cp <= 0xF03D]
    for i, cp in enumerate(component_cps):
        if i >= len(initials):
            break
        key = initials[i]
        component_initials[key] = {
            "codepoint": cp_str(cp),
            "char": char_str(cp),
            "component_slot": i,
        }

    # Syllable rows: one row per initial, columns are finals
    syllable_rows = row_bases[1 : 1 + len(initials)]
    syllables: dict[str, dict] = {}
    syllable_by_cp: dict[str, str] = {}
    missing: list[str] = []

    for ini_idx, initial in enumerate(initials):
        if ini_idx >= len(syllable_rows):
            missing.append(f"initial:{initial}")
            continue
        row_base = syllable_rows[ini_idx]
        row_cells = grid.get(row_base, {})
        for fin_idx, final in enumerate(finals):
            cp = row_cells.get(fin_idx)
            if cp is None:
                missing.append(f"{initial}+{final}")
                continue
            key = f"{initial}+{final}"
            entry = {
                "codepoint": cp_str(cp),
                "char": char_str(cp),
                "initial": initial,
                "final": final,
                "grid": {"row": cp_str(row_base), "col": fin_idx},
            }
            syllables[key] = entry
            syllable_by_cp[cp_str(cp)] = key

    # Overflow rows beyond the 39 initial syllable rows
    overflow: list[dict] = []
    used_rows = set(row_bases[: 1 + len(initials)])
    for row_base in row_bases:
        if row_base in used_rows:
            continue
        for col, cp in sorted(grid[row_base].items()):
            overflow.append(
                {
                    "codepoint": cp_str(cp),
                    "char": char_str(cp),
                    "grid": {"row": cp_str(row_base), "col": col},
                    "syllable_key": syllable_by_cp.get(cp_str(cp)),
                }
            )

    # Parse romanization strings like "taon" by longest-match on initials then finals
    def split_syllable(text: str) -> tuple[str, str] | None:
        text = text.strip().lower()
        if not text:
            return None
        best: tuple[str, str] | None = None
        for ini in sorted(initials, key=len, reverse=True):
            if not text.startswith(ini):
                continue
            rest = text[len(ini) :]
            for fin in sorted(finals, key=len, reverse=True):
                if rest == fin:
                    return ini, fin
        return None

    romanization_lookup: dict[str, dict] = {}
    romanization_unparsed: list[str] = []

    # Build from syllable keys without separator
    for key, entry in syllables.items():
        ini, fin = entry["initial"], entry["final"]
        compact = ini + fin
        if compact not in romanization_lookup:
            romanization_lookup[compact] = {
                "codepoint": entry["codepoint"],
                "char": entry["char"],
                "parse": {"initial": ini, "final": fin},
            }

    # Multi-syllable words from reference RTF (space-separated)
    reference_words = {
        "taon nyie": ["taon", "nyie"],
        "taon nyiq": ["taon", "nyiq"],
        "zie se nyie": ["zie", "se", "nyie"],
        "gheu se nyie": ["gheu", "se", "nyie"],
        "khe nyie": ["khe", "nyie"],
        "le nyie": ["le", "nyie"],
    }
    reference_parses: dict[str, list] = {}
    for phrase, parts in reference_words.items():
        parsed = []
        for part in parts:
            split = split_syllable(part)
            if split:
                ini, fin = split
                syl_key = f"{ini}+{fin}"
                parsed.append(
                    {
                        "romanization": part,
                        "parse": {"initial": ini, "final": fin},
                        "syllable_key": syl_key,
                        "mapping": syllables.get(syl_key),
                    }
                )
            else:
                parsed.append({"romanization": part, "parse": None})
                romanization_unparsed.append(part)
        reference_parses[phrase] = parsed

    grammar = {}
    for marker in manifest.get("grammar_markers", []):
        cp = int(marker["codepoint"].replace("U+", ""), 16)
        grammar[marker["key"]] = {
            "codepoint": cp_str(cp),
            "char": char_str(cp),
            "note": marker.get("note", ""),
            "grid_match": syllable_by_cp.get(cp_str(cp)),
        }

    return {
        "meta": {
            "font": "../goetsusioji-reference/goetsusioji.ttf",
            "pua_range": "U+F021..U+F545",
            "total_pua_glyphs": len([cp for cp in cmap if 0xF021 <= cp <= 0xF545]),
            "grid_rows": len(row_bases),
            "initial_count": len(initials),
            "final_count": len(finals),
            "syllable_entries": len(syllables),
            "missing_cells": missing,
            "unparsed_reference_syllables": sorted(set(romanization_unparsed)),
        },
        "initials": component_initials,
        "finals_order": finals,
        "initials_order": initials,
        "syllables": syllables,
        "romanization": romanization_lookup,
        "grammar": grammar,
        "overflow": overflow,
        "reference_parses": reference_parses,
        "compose": manifest.get("compose", {}),
        "medials": manifest.get("medials", []),
        "tones": manifest.get("tones", []),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping = build()

    full_path = OUT_DIR / "goetsuese-mapping.json"
    with full_path.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    # Convenience extracts
    syllables_path = OUT_DIR / "syllables.json"
    with syllables_path.open("w", encoding="utf-8") as f:
        json.dump(mapping["syllables"], f, ensure_ascii=False, indent=2)

    romanization_path = OUT_DIR / "romanization.json"
    with romanization_path.open("w", encoding="utf-8") as f:
        json.dump(mapping["romanization"], f, ensure_ascii=False, indent=2)

    components_path = OUT_DIR / "components.json"
    with components_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "initials": mapping["initials"],
                "medials": mapping["medials"],
                "tones": mapping["tones"],
                "grammar": mapping["grammar"],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Wrote {full_path}")
    print(f"  syllables: {mapping['meta']['syllable_entries']}")
    print(f"  components: {len(mapping['initials'])}")
    print(f"  romanization keys: {len(mapping['romanization'])}")
    if mapping["meta"]["missing_cells"]:
        print(f"  missing cells: {len(mapping['meta']['missing_cells'])}")
    if mapping["meta"]["unparsed_reference_syllables"]:
        print(f"  unparsed reference: {mapping['meta']['unparsed_reference_syllables']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
