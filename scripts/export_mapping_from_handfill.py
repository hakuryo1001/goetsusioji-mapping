#!/usr/bin/env python3
"""Export mapping/goetsuese-mapping.json from data/glyphs-handfill.json (as-is romanizations)."""

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
HANDFILL_JSON = ROOT / "data" / "glyphs-handfill.json"
HANDFILL_MD = ROOT / "data" / "chart-tables-handfill.md"
OUT_PATH = ROOT / "mapping" / "goetsuese-mapping.json"

SYLLABLE_GRID_START = 0xF040
SYLLABLE_ROW_STRIDE = 0x20
SYLLABLE_ROWS = 38
FINAL_HEADER_START = 0xF021
FINAL_HEADER_COUNT = 25
HEADER_ROW_BASE = 0xF020
GRAMMAR_TSY_CP = 0xF3CA
COMPONENT_RANGE = range(0xF500, 0xF546)

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


def syllable_row_bases() -> list[int]:
    return [SYLLABLE_GRID_START + i * SYLLABLE_ROW_STRIDE for i in range(SYLLABLE_ROWS)]


def finals_order(glyphs: dict[str, dict]) -> list[str]:
    order: list[str] = []
    for offset in range(FINAL_HEADER_COUNT):
        key = cp_str(FINAL_HEADER_START + offset)
        romanization = glyphs[key].get("romanization", "").strip()
        if not romanization:
            raise ValueError(f"missing header final at {key}; fill U+F021..U+F039 first")
        order.append(romanization)
    return order


def normalize_component_key(romanization: str) -> str | None:
    text = romanization.strip()
    if not text:
        return None
    return COMPONENT_ROMANIZATION_ALIASES.get(text, text)


def component_keys_from_romanization(romanization: str) -> list[str]:
    keys: list[str] = []
    for part in romanization.split("|"):
        key = normalize_component_key(part.strip())
        if key and key not in keys:
            keys.append(key)
    return keys


def parse_syllable(compact: str, row_initial: str, col: int, finals: list[str]) -> tuple[str, str] | None:
    compact = compact.strip()
    if not compact or col < 1 or col > 25:
        return None
    final = finals[col - 1]
    if row_initial == "-":
        if compact.startswith("-"):
            rest = compact[1:]
            if rest:
                return "null", rest
        return None
    if compact.endswith(final):
        initial = compact[: -len(final)]
        if initial:
            return initial, final
        if compact == final:
            return row_initial, final
    if compact.startswith(row_initial):
        rest = compact[len(row_initial) :]
        if rest:
            return row_initial, rest
    if compact.startswith("-"):
        rest = compact[1:]
        if rest:
            return "null", rest
    return None


def enumerate_grid(cmap: dict[int, str]) -> tuple[list[int], dict[int, dict[int, int]]]:
    rows: list[int] = []
    grid: dict[int, dict[int, int]] = {}
    for cp in sorted(c for c in cmap if 0xF021 <= c <= 0xF545):
        col = cp & 0x1F
        if col >= 26:
            continue
        row_base = cp & 0xFFE0
        if row_base not in grid:
            grid[row_base] = {}
            rows.append(row_base)
        grid[row_base][col] = cp
    return rows, grid


def merge_chart_metadata(comp: dict, hand: dict, kind: str, key: str) -> dict:
    chart = hand["initials" if kind == "initial" else "finals"].get(key, {})
    merged = {**comp}
    if chart.get("group"):
        merged["group"] = chart["group"]
    if chart.get("source"):
        merged["source"] = chart["source"]
    return merged


def components_from_glyphs(glyphs: dict[str, dict], hand: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    component_initials: dict[str, dict] = {}
    component_finals: dict[str, dict] = {}

    for cp in COMPONENT_RANGE:
        key = cp_str(cp)
        entry = glyphs.get(key)
        if not entry:
            continue
        role = entry.get("role", "")
        if not role:
            continue
        romanization = entry.get("romanization", "").strip()
        if not romanization:
            continue

        base = {
            "codepoint": key,
            "char": entry["char"],
        }
        if entry.get("notes"):
            base["notes"] = entry["notes"]

        if "initial" in role:
            for comp_key in component_keys_from_romanization(romanization):
                component_initials[comp_key] = merge_chart_metadata(
                    base, hand, "initial", comp_key
                )
        if "final" in role:
            for comp_key in component_keys_from_romanization(romanization):
                component_finals[comp_key] = merge_chart_metadata(
                    base, hand, "final", comp_key
                )

    return component_initials, component_finals


def build_mapping(glyphs: dict[str, dict], manifest: dict, hand: dict, cmap: dict[int, str]) -> dict:
    initials_order = [entry["key"] for entry in manifest["initials"]]
    grid_finals = finals_order(glyphs)
    row_bases, grid = enumerate_grid(cmap)
    syllable_rows = syllable_row_bases()

    component_initials, component_finals = components_from_glyphs(glyphs, hand)

    syllables: dict[str, dict] = {}
    grid_initials: dict[str, dict] = {}
    romanization_lookup: dict[str, dict] = {}
    duplicate_compact: list[str] = []
    unparsed_syllables: list[str] = []
    filled_syllable_cells = 0

    for row_base in syllable_rows:
        row_cells = grid.get(row_base, {})
        cp0 = row_cells.get(0)
        if cp0 is None:
            continue
        row_initial = glyphs.get(cp_str(cp0), {}).get("romanization", "").strip()
        if not row_initial:
            continue

        grid_initials[row_initial] = {
            "codepoint": cp_str(cp0),
            "char": chr(cp0),
            "initial": row_initial if row_initial != "-" else "null",
            "grid": {"row": cp_str(row_base), "col": 0},
        }
        if row_initial not in romanization_lookup:
            romanization_lookup[row_initial] = {
                "codepoint": cp_str(cp0),
                "char": chr(cp0),
                "kind": "grid_initial",
                "initial": row_initial if row_initial != "-" else "null",
                "note": "initial-only composed row header (chart grid col 0)",
            }

        for col in range(1, 26):
            cp = row_cells.get(col)
            if cp is None:
                continue
            compact = glyphs.get(cp_str(cp), {}).get("romanization", "").strip()
            if not compact:
                continue
            filled_syllable_cells += 1

            parsed = parse_syllable(compact, row_initial, col, grid_finals)
            if parsed is None:
                unparsed_syllables.append(f"{cp_str(cp)}:{compact}")
                continue
            initial, final = parsed
            if initial == "-":
                initial = "null"

            entry = {
                "codepoint": cp_str(cp),
                "char": chr(cp),
                "initial": initial,
                "final": final,
                "grid": {"row": cp_str(row_base), "col": col},
                "romanization": compact,
            }
            syl_key = f"{initial}+{final}"
            if syl_key in syllables and syllables[syl_key]["codepoint"] != entry["codepoint"]:
                syl_key = f"{initial}+{final}@{cp_str(cp)}"
            syllables[syl_key] = entry

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

    for cp in COMPONENT_RANGE:
        key = cp_str(cp)
        entry = glyphs.get(key)
        if not entry:
            continue
        romanization = entry.get("romanization", "").strip()
        if not romanization or romanization in romanization_lookup:
            continue
        role = entry.get("role", "")
        kind = None
        if "initial" in role:
            kind = "initial"
        elif "final" in role:
            kind = "final"
        if kind:
            romanization_lookup[romanization] = {
                "codepoint": key,
                "char": entry["char"],
                "kind": kind,
                "note": "component glyph romanization (exact handfill string)",
            }

    grammar: dict[str, dict] = {}
    tsy_entry = glyphs.get(cp_str(GRAMMAR_TSY_CP), {})
    tsy_roman = tsy_entry.get("romanization", "").strip() or "tsy"
    grammar["tsy"] = {
        "codepoint": cp_str(GRAMMAR_TSY_CP),
        "char": chr(GRAMMAR_TSY_CP),
        "note": next(
            (m.get("note", "") for m in manifest.get("grammar_markers", []) if m.get("key") == "tsy"),
            "",
        ),
        "grid_match": romanization_lookup.get(tsy_roman, {}).get("codepoint"),
    }
    if tsy_roman not in romanization_lookup:
        romanization_lookup[tsy_roman] = {
            "codepoint": cp_str(GRAMMAR_TSY_CP),
            "char": chr(GRAMMAR_TSY_CP),
            "kind": "grammar",
            "note": grammar["tsy"]["note"],
        }

    overflow: list[dict] = []
    used_rows = {HEADER_ROW_BASE, *syllable_rows}
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
            "handfill_source": str(HANDFILL_JSON.relative_to(ROOT)),
            "derivation": (
                "Syllable grid romanizations read as-is from glyphs-handfill.json. "
                "Col 0 rows U+F040..U+F4E0 (stride 0x20); cols 1..25 follow header finals U+F021..U+F039. "
                "Components from glyphs with role initial/final (U+F500..F545), groups merged from chart-tables-handfill.md."
            ),
            "pua_range": "U+F021..U+F545",
            "syllable_grid": "U+F040..U+F4F9",
            "component_table": "U+F500..F545",
            "total_pua_glyphs": len([cp for cp in cmap if 0xF021 <= cp <= 0xF545]),
            "grid_rows": len(row_bases),
            "syllable_row_count": SYLLABLE_ROWS,
            "initial_count": len(initials_order),
            "grid_final_count": len(grid_finals),
            "syllable_entries": len(syllables),
            "expected_syllable_entries": filled_syllable_cells,
            "grid_initial_entries": len(grid_initials),
            "romanization_entries": len(romanization_lookup),
            "romanization_by_kind": by_kind,
            "component_initials": len(component_initials),
            "component_finals": len(component_finals),
            "duplicate_compact_romanizations": sorted(set(duplicate_compact)),
            "unparsed_syllable_cells": unparsed_syllables,
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
    if not HANDFILL_JSON.exists():
        print(f"Missing {HANDFILL_JSON}", file=sys.stderr)
        return 1
    if not FONT_PATH.exists():
        print(f"Missing font {FONT_PATH}", file=sys.stderr)
        return 1

    data = load_json(HANDFILL_JSON)
    glyphs = data["glyphs"]
    manifest = load_json(MANIFEST_PATH)
    hand = load_hand_curated()
    cmap = TTFont(FONT_PATH).getBestCmap()
    mapping = build_mapping(glyphs, manifest, hand, cmap)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    meta = mapping["meta"]
    print(f"Wrote {OUT_PATH}")
    print(f"  syllables: {meta['syllable_entries']} (filled cells: {meta['expected_syllable_entries']})")
    print(f"  grid initials: {meta['grid_initial_entries']}")
    print(f"  romanization: {meta['romanization_entries']} {meta['romanization_by_kind']}")
    if meta["duplicate_compact_romanizations"]:
        print(f"  duplicate compact strings: {meta['duplicate_compact_romanizations']}")
    if meta["unparsed_syllable_cells"]:
        print(f"  unparsed cells: {len(meta['unparsed_syllable_cells'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
