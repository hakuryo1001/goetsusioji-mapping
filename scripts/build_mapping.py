#!/usr/bin/env python3
"""Build full Goetsuese romanization → PUA mapping from hand-fill + font syllable grid."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT.parent / "goetsusioji-reference"
FONT_PATH = REF / "goetsusioji.ttf"
MANIFEST_PATH = ROOT / "data" / "chart-manifest.json"
HANDFILL_PATH = ROOT / "data" / "chart-tables-handfill.md"
OUT_DIR = ROOT / "mapping"

COMPONENT_RANGE = range(0xF500, 0xF546)


def load_manifest() -> dict:
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_hand_curated() -> dict:
    spec = importlib.util.spec_from_file_location(
        "parse_handfill", ROOT / "scripts" / "parse_handfill.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load parse_handfill.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_handfill(HANDFILL_PATH)


def enumerate_grid(cmap: dict[int, str]) -> tuple[list[int], dict[int, dict[int, int]]]:
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


def entry_from_component(key: str, comp: dict, kind: str) -> dict:
    return {
        "codepoint": comp["codepoint"],
        "char": comp["char"],
        "kind": kind,
        "key": key,
    }


def build() -> dict:
    manifest = load_manifest()
    hand = load_hand_curated()
    initials = [x["key"] for x in manifest["initials"]]
    finals = [x["key"] for x in manifest["finals"]]

    font = TTFont(FONT_PATH)
    cmap = font.getBestCmap()
    row_bases, grid = enumerate_grid(cmap)

    component_initials: dict[str, dict] = {}
    for key in initials:
        comp = hand["initials"].get(key)
        if comp:
            component_initials[key] = {**comp}

    component_finals: dict[str, dict] = {}
    for key in finals:
        comp = hand["finals"].get(key)
        if comp:
            component_finals[key] = {**comp}

    component_medials: dict[str, dict] = {}
    for medial in manifest.get("medials", []):
        key = medial["key"]
        comp = hand["medials"].get(key)
        if comp:
            component_medials[key] = {
                **comp,
                "label": medial.get("label"),
            }

    # Chart grid: row = initial (manifest order), column = final (manifest order).
    # Each cell is a pre-composed syllable glyph in the font (not computed from components).
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
                    "role": "component_table" if cp in COMPONENT_RANGE else "overflow",
                    "grid": {"row": cp_str(row_base), "col": col},
                    "syllable_key": syllable_by_cp.get(cp_str(cp)),
                }
            )

    def split_syllable(text: str) -> tuple[str, str] | None:
        text = text.strip().lower()
        if not text:
            return None
        for ini in sorted(initials, key=len, reverse=True):
            if not text.startswith(ini):
                continue
            rest = text[len(ini) :]
            for fin in sorted(finals, key=len, reverse=True):
                if rest == fin:
                    return ini, fin
        return None

    # Full romanization → glyph table (the main lookup surface).
    romanization_lookup: dict[str, dict] = {}
    romanization_unparsed: list[str] = []

    for key, entry in syllables.items():
        ini, fin = entry["initial"], entry["final"]
        compact = ini + fin
        romanization_lookup[compact] = {
            "codepoint": entry["codepoint"],
            "char": entry["char"],
            "kind": "syllable",
            "parse": {"initial": ini, "final": fin},
        }

    # Standalone onset components (chart 1 — initial-only forms like ph, not pha).
    for key, comp in component_initials.items():
        if key not in romanization_lookup:
            romanization_lookup[key] = {
                **entry_from_component(key, comp, "initial"),
                "note": "initial-only component; not a composed syllable",
            }

    # Standalone rime components (chart 2).
    for key, comp in component_finals.items():
        if key not in romanization_lookup:
            romanization_lookup[key] = {
                **entry_from_component(key, comp, "final"),
                "note": "final-only component",
            }

    grammar: dict[str, dict] = {}
    for marker in manifest.get("grammar_markers", []):
        cp = int(marker["codepoint"].replace("U+", ""), 16)
        grammar[marker["key"]] = {
            "codepoint": cp_str(cp),
            "char": char_str(cp),
            "note": marker.get("note", ""),
            "grid_match": syllable_by_cp.get(cp_str(cp)),
        }
        romanization_lookup[marker["key"]] = {
            "codepoint": cp_str(cp),
            "char": char_str(cp),
            "kind": "grammar",
            "note": marker.get("note", ""),
        }

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
            elif part in romanization_lookup:
                parsed.append(
                    {
                        "romanization": part,
                        "mapping": romanization_lookup[part],
                    }
                )
            else:
                parsed.append({"romanization": part, "parse": None})
                romanization_unparsed.append(part)
        reference_parses[phrase] = parsed

    missing_components = [
        f"initial:{k}" for k in initials if k not in component_initials
    ] + [f"final:{k}" for k in finals if k not in component_finals]

    by_kind = {"syllable": 0, "initial": 0, "final": 0, "grammar": 0}
    for entry in romanization_lookup.values():
        by_kind[entry.get("kind", "syllable")] = by_kind.get(entry.get("kind", "syllable"), 0) + 1

    return {
        "meta": {
            "font": "../goetsusioji-reference/goetsusioji.ttf",
            "handfill_source": "data/chart-tables-handfill.md",
            "derivation": (
                "Components from hand-fill (U+F500..F545). "
                "Composed syllables from font grid rows/cols indexed by manifest initial×final order (U+F040..F4F9)."
            ),
            "pua_range": "U+F021..U+F545",
            "syllable_grid": "U+F040..U+F4F9",
            "component_table": "U+F500..U+F545",
            "total_pua_glyphs": len([cp for cp in cmap if 0xF021 <= cp <= 0xF545]),
            "grid_rows": len(row_bases),
            "initial_count": len(initials),
            "final_count": len(finals),
            "syllable_entries": len(syllables),
            "romanization_entries": len(romanization_lookup),
            "romanization_by_kind": by_kind,
            "component_initials": len(component_initials),
            "component_finals": len(component_finals),
            "missing_cells": missing,
            "missing_components": missing_components,
            "handfill_warnings": hand.get("warnings", []),
            "unparsed_reference_syllables": sorted(set(romanization_unparsed)),
        },
        "initials": component_initials,
        "finals": component_finals,
        "finals_order": finals,
        "initials_order": initials,
        "syllables": syllables,
        "romanization": romanization_lookup,
        "grammar": grammar,
        "overflow": overflow,
        "reference_parses": reference_parses,
        "compose": manifest.get("compose", {}),
        "medials": component_medials or manifest.get("medials", []),
        "tones": manifest.get("tones", []),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping = build()

    full_path = OUT_DIR / "goetsuese-mapping.json"
    with full_path.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    meta = mapping["meta"]
    print(f"Wrote {full_path}")
    print(f"  romanization entries: {meta['romanization_entries']} {meta['romanization_by_kind']}")
    print(f"  syllables: {meta['syllable_entries']}")
    print(f"  components: {meta['component_initials']} initials, {meta['component_finals']} finals")
    if meta["missing_components"]:
        print(f"  missing components: {meta['missing_components']}")
    if meta["handfill_warnings"]:
        print(f"  handfill warnings: {meta['handfill_warnings']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
