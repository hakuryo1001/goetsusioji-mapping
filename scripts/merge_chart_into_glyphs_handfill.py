#!/usr/bin/env python3
"""Merge romanizations from chart-tables-handfill.md into glyphs-handfill.json."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHART_PATH = ROOT / "data" / "chart-tables-handfill.md"
GLYPHS_PATH = ROOT / "data" / "glyphs-handfill.json"


def load_parse_handfill():
    spec = importlib.util.spec_from_file_location(
        "parse_handfill", ROOT / "scripts" / "parse_handfill.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def collect_chart_entries() -> dict[str, list[dict]]:
    """codepoint -> [{romanization, role, group}]"""
    mod = load_parse_handfill()
    text = CHART_PATH.read_text(encoding="utf-8")
    s1 = text.find("# Section 1")
    s2 = text.find("# Section 2")
    s3 = text.find("# Section 3")
    s31 = text.find("## 3.1")

    by_cp: dict[str, list[dict]] = {}

    def add(cp: int, romanization: str, role: str, group: str = "") -> None:
        raw = romanization.strip().strip("*")
        if not raw or raw.startswith("("):
            return
        key = f"U+{cp:04X}"
        entry = {"romanization": raw, "role": role}
        if group:
            entry["group"] = group
        by_cp.setdefault(key, [])
        if not any(e["romanization"] == raw and e["role"] == role for e in by_cp[key]):
            by_cp[key].append(entry)

    for romanization, glyph, codepoint_col, group in mod.parse_table_rows(text[s1:s2]):
        norm = mod.normalize_romanization(romanization)
        if norm is None:
            continue
        if norm == "…":
            rom = "zero" if group == "零聲母" else "null" if group == "奥" else None
            if rom is None:
                continue
            raw = rom
        else:
            raw = romanization.strip().strip("*")
        cp = mod.extract_codepoint(glyph, codepoint_col)
        if cp is None:
            continue
        add(cp, raw, "initial", group)

    for romanization, glyph, codepoint_col, group in mod.parse_table_rows(text[s2:s3]):
        if mod.normalize_romanization(romanization) is None:
            continue
        cp = mod.extract_codepoint(glyph, codepoint_col)
        if cp is None:
            continue
        add(cp, romanization.strip().strip("*"), "final", group or "finals-grid")

    for romanization, glyph, codepoint_col, _group in mod.parse_table_rows(text[s3:s31]):
        if mod.normalize_romanization(romanization) is None:
            continue
        cp = mod.extract_codepoint(glyph, codepoint_col)
        if cp is None:
            continue
        add(cp, romanization.strip().strip("*"), "medial")

    return by_cp


def merge_romanization(entries: list[dict]) -> str:
    seen: list[str] = []
    for e in entries:
        r = e["romanization"]
        if r not in seen:
            seen.append(r)
    return " | ".join(seen)


def roles_summary(entries: list[dict]) -> str | None:
    roles = sorted({e["role"] for e in entries})
    if len(roles) == 1:
        return roles[0]
    return " | ".join(roles)


def merge() -> dict:
    chart = collect_chart_entries()
    data = json.loads(GLYPHS_PATH.read_text(encoding="utf-8"))

    # Reset chart-derived fields so corrections in the markdown propagate cleanly.
    for entry in data["glyphs"].values():
        entry["romanization"] = ""
        entry.pop("role", None)
        entry.pop("notes", None)

    filled = 0
    shared: list[str] = []

    for cp_key, entry in data["glyphs"].items():
        if cp_key not in chart:
            continue
        items = chart[cp_key]
        entry["romanization"] = merge_romanization(items)
        role = roles_summary(items)
        if role:
            entry["role"] = role
        if len(items) > 1:
            entry["notes"] = "; ".join(
                f"{i['romanization']} ({i['role']})" for i in items
            )
            shared.append(cp_key)
        filled += 1

    data["meta"]["filled_from_chart"] = filled
    data["meta"]["chart_source"] = "data/chart-tables-handfill.md"
    data["meta"]["shared_glyphs"] = shared

    unfilled_chart = sorted(set(chart) - set(data["glyphs"]))
    if unfilled_chart:
        data["meta"]["chart_codepoints_not_in_font"] = unfilled_chart

    return data


def main() -> int:
    if not GLYPHS_PATH.exists():
        print(f"Missing {GLYPHS_PATH}; run export_glyphs_handfill.py first", file=sys.stderr)
        return 1
    data = merge()
    GLYPHS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {GLYPHS_PATH}")
    print(f"  filled: {data['meta']['filled_from_chart']} glyphs from chart")
    shared = data["meta"].get("shared_glyphs", [])
    if shared:
        print(f"  shared glyphs ({len(shared)}): {', '.join(shared)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
