#!/usr/bin/env python3
"""Fill syllable grid romanizations and export mapping/goetsuese-mapping.json."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT.parent / "goetsusioji-reference"
FONT_PATH = REF / "goetsusioji.ttf"
MANIFEST_PATH = ROOT / "data" / "chart-manifest.json"
DEFAULT_INPUT = ROOT / "data" / "glyphs-handfill-original.json"
DEFAULT_OUTPUT = ROOT / "mapping" / "goetsuese-mapping.json"
HANDFILL_MD = ROOT / "data" / "chart-tables-handfill.md"

SYLLABLE_GRID_START = 0xF040
SYLLABLE_ROW_STRIDE = 0x20
SYLLABLE_ROWS = 38  # ph .. u (w has no syllable row; see U+F544)
FINAL_HEADER_START = 0xF021
FINAL_HEADER_COUNT = 25  # cols 1..25 in each syllable row
COMPONENT_RANGE = range(0xF500, 0xF546)

ROMANIZATION_OVERRIDES: dict[str, str] = {
    "U+F3CA": "tsy",
}

COMPONENT_ROMANIZATION_ALIASES = {
    "ch(i)": "ch",
    "c(i)": "c",
    "j(i)": "j",
    "sh(i)": "sh",
    "zh(i)": "zh",
    "ae(n)": "ae",
    "oe(n)": "oe",
    "ie(n)": "ie",
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_hand_curated() -> dict:
    spec = importlib.util.spec_from_file_location(
        "parse_handfill", ROOT / "scripts" / "parse_handfill.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load parse_handfill.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_handfill(HANDFILL_MD)


def cp_str(cp: int) -> str:
    return f"U+{cp:04X}"


def finals_order(glyphs: dict[str, dict]) -> list[str]:
    order: list[str] = []
    for offset in range(FINAL_HEADER_COUNT):
        key = f"U+{FINAL_HEADER_START + offset:04X}"
        romanization = glyphs[key].get("romanization", "").strip()
        if not romanization:
            raise ValueError(f"missing header final at {key}; fill U+F021..U+F039 first")
        order.append(romanization)
    return order


def syllable_romanization(initial: str, col: int, finals: list[str]) -> str:
    if col == 0:
        return initial
    return initial + finals[col - 1]


def fill_grid_entries(glyphs: dict[str, dict], initials: list[str], finals: list[str]) -> tuple[int, int]:
    filled = 0
    kept = 0

    for row_idx, initial in enumerate(initials[:SYLLABLE_ROWS]):
        row_base = SYLLABLE_GRID_START + row_idx * SYLLABLE_ROW_STRIDE
        for col in range(26):
            cp = row_base + col
            key = cp_str(cp)
            if key not in glyphs:
                continue

            entry = glyphs[key]
            if entry.get("romanization", "").strip():
                kept += 1
                continue

            if key in ROMANIZATION_OVERRIDES:
                entry["romanization"] = ROMANIZATION_OVERRIDES[key]
            else:
                entry["romanization"] = syllable_romanization(initial, col, finals)
            filled += 1

    return filled, kept


def enumerate_grid(cmap: dict[int, str]) -> tuple[list[int], dict[int, dict[int, int]]]:
    rows: list[int] = []
    grid: dict[int, dict[int, int]] = {}
    for cp in sorted(cp for cp in cmap if 0xF021 <= cp <= 0xF545):
        col = cp & 0x1F
        if col >= 26:
            continue
        row_base = cp & 0xFFE0
        if row_base not in grid:
            grid[row_base] = {}
            rows.append(row_base)
        grid[row_base][col] = cp
    return rows, grid


def normalize_component_key(romanization: str) -> str | None:
    text = romanization.strip()
    if not text:
        return None
    if "|" in text:
        text = text.split("|", 1)[0].strip()
    return COMPONENT_ROMANIZATION_ALIASES.get(text, text)


def build_mapping(glyphs: dict[str, dict], manifest: dict, hand: dict, cmap: dict[int, str]) -> dict:
    initials_order = [entry["key"] for entry in manifest["initials"]]
    grid_finals = finals_order(glyphs)
    row_bases, grid = enumerate_grid(cmap)
    syllable_rows = row_bases[1 : 1 + SYLLABLE_ROWS]

    component_initials: dict[str, dict] = {}
    for key in initials_order:
        comp = hand["initials"].get(key)
        if comp:
            component_initials[key] = {**comp}

    component_finals: dict[str, dict] = {}
    manifest_final_keys = [entry["key"] for entry in manifest["finals"]]
    for key in manifest_final_keys:
        comp = hand["finals"].get(key)
        if comp:
            component_finals[key] = {**comp}

    syllables: dict[str, dict] = {}
    grid_initials: dict[str, dict] = {}
    romanization_lookup: dict[str, dict] = {}
    duplicate_compact: list[str] = []

    for row_idx, initial in enumerate(initials_order[:SYLLABLE_ROWS]):
        row_base = syllable_rows[row_idx]
        row_cells = grid.get(row_base, {})

        cp0 = row_cells.get(0)
        if cp0 is not None:
            compact0 = initial
            grid_initials[initial] = {
                "codepoint": cp_str(cp0),
                "char": chr(cp0),
                "initial": initial,
                "grid": {"row": cp_str(row_base), "col": 0},
            }
            if compact0 not in romanization_lookup:
                romanization_lookup[compact0] = {
                    "codepoint": cp_str(cp0),
                    "char": chr(cp0),
                    "kind": "grid_initial",
                    "initial": initial,
                    "note": "initial-only composed row header (chart grid col 0)",
                }

        for col in range(1, 26):
            cp = row_cells.get(col)
            if cp is None:
                continue
            final = grid_finals[col - 1]
            compact = initial + final
            entry = {
                "codepoint": cp_str(cp),
                "char": chr(cp),
                "initial": initial,
                "final": final,
                "grid": {"row": cp_str(row_base), "col": col},
            }
            key = f"{initial}+{final}"
            if key in syllables and syllables[key]["codepoint"] != entry["codepoint"]:
                key = f"{initial}+{final}@col{col}"
            syllables[key] = entry

            if compact in romanization_lookup and romanization_lookup[compact]["codepoint"] != entry["codepoint"]:
                duplicate_compact.append(compact)
            romanization_lookup[compact] = {
                "codepoint": entry["codepoint"],
                "char": entry["char"],
                "kind": "syllable",
                "parse": {"initial": initial, "final": final},
            }

    for key, comp in component_initials.items():
        if key not in romanization_lookup:
            romanization_lookup[key] = {
                "codepoint": comp["codepoint"],
                "char": comp["char"],
                "kind": "initial",
                "key": key,
                "note": "initial-only component; not a composed syllable",
            }

    for key, comp in component_finals.items():
        if key not in romanization_lookup:
            romanization_lookup[key] = {
                "codepoint": comp["codepoint"],
                "char": comp["char"],
                "kind": "final",
                "key": key,
                "note": "final-only component",
            }

    grammar: dict[str, dict] = {}
    for marker in manifest.get("grammar_markers", []):
        cp = int(marker["codepoint"].replace("U+", ""), 16)
        grammar[marker["key"]] = {
            "codepoint": cp_str(cp),
            "char": chr(cp),
            "note": marker.get("note", ""),
            "grid_match": None,
        }
        romanization_lookup[marker["key"]] = {
            "codepoint": cp_str(cp),
            "char": chr(cp),
            "kind": "grammar",
            "note": marker.get("note", ""),
        }

    overflow: list[dict] = []
    used_rows = set(row_bases[: 1 + SYLLABLE_ROWS])
    syllable_by_cp = {entry["codepoint"]: key for key, entry in syllables.items()}
    for row_base in row_bases:
        if row_base in used_rows:
            continue
        for col, cp in sorted(grid.get(row_base, {}).items()):
            overflow.append(
                {
                    "codepoint": cp_str(cp),
                    "char": chr(cp),
                    "role": "component_table" if cp in COMPONENT_RANGE else "overflow",
                    "grid": {"row": cp_str(row_base), "col": col},
                    "syllable_key": syllable_by_cp.get(cp_str(cp)),
                    "romanization": glyphs.get(cp_str(cp), {}).get("romanization", ""),
                }
            )

    by_kind: dict[str, int] = {}
    for entry in romanization_lookup.values():
        kind = entry.get("kind", "syllable")
        by_kind[kind] = by_kind.get(kind, 0) + 1

    return {
        "meta": {
            "font": "../goetsusioji-reference/goetsusioji.ttf",
            "handfill_source": str(DEFAULT_INPUT.relative_to(ROOT)),
            "derivation": (
                "Syllable grid from U+F040..U+F4F9: col 0 = initial-only, cols 1..25 follow "
                "header finals U+F021..U+F039. Components from chart-tables-handfill.md (U+F500..F545)."
            ),
            "pua_range": "U+F021..U+F545",
            "syllable_grid": "U+F040..U+F4F9",
            "component_table": "U+F500..U+F545",
            "total_pua_glyphs": len([cp for cp in cmap if 0xF021 <= cp <= 0xF545]),
            "grid_rows": len(row_bases),
            "syllable_row_count": SYLLABLE_ROWS,
            "initial_count": len(initials_order),
            "grid_final_count": len(grid_finals),
            "syllable_entries": len(syllables),
            "grid_initial_entries": len(grid_initials),
            "romanization_entries": len(romanization_lookup),
            "romanization_by_kind": by_kind,
            "component_initials": len(component_initials),
            "component_finals": len(component_finals),
            "duplicate_compact_romanizations": sorted(set(duplicate_compact)),
            "handfill_warnings": hand.get("warnings", []),
        },
        "initials": component_initials,
        "finals": component_finals,
        "finals_order": grid_finals,
        "initials_order": initials_order,
        "grid_initials": grid_initials,
        "syllables": syllables,
        "romanization": romanization_lookup,
        "grammar": grammar,
        "overflow": overflow,
        "compose": manifest.get("compose", {}),
        "medials": manifest.get("medials", []),
        "tones": manifest.get("tones", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Missing {args.input}", file=sys.stderr)
        return 1
    if not FONT_PATH.exists():
        print(f"Missing font {FONT_PATH}", file=sys.stderr)
        return 1

    data = load_json(args.input)
    glyphs = data["glyphs"]
    manifest = load_json(MANIFEST_PATH)
    hand = load_hand_curated()
    initials = [entry["key"] for entry in manifest["initials"]]
    finals = finals_order(glyphs)

    filled, kept = fill_grid_entries(glyphs, initials, finals)
    mapping = build_mapping(glyphs, manifest, hand, TTFont(FONT_PATH).getBestCmap())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    meta = mapping["meta"]
    print(f"Wrote {args.output}")
    print(f"  grid fill: {filled} new, {kept} kept from {args.input.name}")
    print(f"  syllables: {meta['syllable_entries']} (+ {meta['grid_initial_entries']} grid initials)")
    print(f"  romanization: {meta['romanization_entries']} {meta['romanization_by_kind']}")
    if meta["duplicate_compact_romanizations"]:
        print(f"  duplicate compact strings: {meta['duplicate_compact_romanizations']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
