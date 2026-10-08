#!/usr/bin/env python3
"""Fill chinese character only orthography from initial+final tables.

Reads handfilling/glyphs-handfill-with-chinese.json, fills only empty Chinese
hints into derived/glyphs-with-chinese.json, and writes a validation report for
already-filled entries. Does not modify handfilling/.

Chart vs handfill notes
-----------------------
- Final ``y``: pic 2 labels 私(空韻); handfill/this filler use 厶.
- Fricatives f/s/sh: pic 1 draws ゜ on the Goetsu glyphs; Chinese *hints* in
  handfill omit ﾟ (弗/兴/式). This filler keeps the handfill convention.
- Final ``oq``: pic 2 and handfill both use 昱.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "handfilling" / "glyphs-handfill-with-chinese.json"
DEFAULT_OUTPUT = ROOT / "derived" / "glyphs-with-chinese.json"
DEFAULT_REPORT = ROOT / "derived" / "validation-report.md"

CHINESE_KEY = "chinese character only orthography"

# Handfill-consistent final example Han.
# Note: chart pic 2 labels y as 私(空韻); we keep handfill 厶.
FINAL_HAN: dict[str, str] = {
    "a": "派",
    "aq": "乏",
    "o": "瓦",
    "oq": "昱",
    "e": "卑",
    "eq": "出",
    "i": "以",
    "iq": "亦",
    "u": "无",
    "y": "厶",
    "ae": "万",
    "ie": "建",
    "au": "号",
    "ou": "多",
    "eu": "久",
    "iu": "雨",
    "oe": "寒",
    "an": "良",
    "on": "从",
    "en": "文",
    "in": "刃",
    "aon": "亡",
    "eon": "能",
    "r": "而",
}

# Chart group Han + diacritic (ﾟ aspirated/clear, ﾞ voiced).
# Pic 1 shows ゜ on f/sh/s Goetsu glyphs; Chinese hints stay unmarked per handfill.
INITIAL_MARKER: dict[str, str] = {
    "ph": "兵ﾟ",
    "p": "兵",
    "b": "兵ﾞ",
    "th": "刀ﾟ",
    "t": "刀",
    "d": "刀ﾞ",
    "kh": "工ﾟ",
    "k": "工",
    "g": "工ﾞ",
    "ch": "斤ﾟ",
    "c": "斤",
    "j": "斤ﾞ",
    "tsh": "子ﾟ",
    "ts": "子",
    "dz": "子ﾞ",
    "sh": "兴",
    "zh": "兴ﾞ",
    "s": "式",
    "z": "式ﾞ",
    "f": "弗",
    "v": "弗ﾞ",
    "h": "奧ﾟ",
    "-": "奧",
    "gh": "奧ﾞ",
    "m": "矛",
    "mh": "矛ﾟ",
    "n": "拿",
    "nh": "拿ﾟ",
    "l": "力",
    "lh": "力ﾟ",
    "ny": "女",
    "nyh": "女ﾟ",
    "ng": "午",
    "nk": "午ﾟ",
    "i": "云",
    "y": "云",
    "w": "危",
    "u": "危",
}

# Pic 2 coda components and zero-initial aliases (applied before split).
SPECIAL_BY_CODEPOINT: dict[str, str] = {
    "U+F03A": "レ",  # -n coda (兒化/鼻韻尾)
    "U+F03B": "く",  # -q coda (促化/塞韻尾)
    "U+F53A": "レ",  # hn final component
    "U+F53B": "く",  # hq final component
}

SPECIAL_BY_ROMANIZATION: dict[str, str] = {
    "-": "奧",
    "zero | null": "奧",
    "zero": "奧",
    "null": "奧",
}

ROMANIZATION_ALIASES: dict[str, str] = {
    "ch(i)": "ch",
    "c(i)": "c",
    "j(i)": "j",
    "sh(i)": "sh",
    "zh(i)": "zh",
    "ae(n)": "ae",
    "oe(n)": "oe",
    "ie(n)": "ie",
    "mh | m": "mh",
}

# Longest-first so tsh beats ts, nyh beats ny, etc.
_INITIALS_SORTED = sorted(INITIAL_MARKER.keys(), key=len, reverse=True)

# Bare romanizations that are both a final and an onset (云 / 危 groups).
_AMBIGUOUS_ONSET_FINALS = frozenset({"i", "y", "u"})

# Chart-2 final header + coda slots (handfill uses these as pure finals).
_FINAL_HEADER_RANGE = range(0xF021, 0xF040)


def normalize_romanization(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    if text in ROMANIZATION_ALIASES:
        return ROMANIZATION_ALIASES[text]
    # Strip trailing parenthetical notes: ie(n) already covered; be defensive.
    text = re.sub(r"\([^)]*\)$", "", text).strip()
    if " | " in text:
        text = text.split(" | ", 1)[0].strip()
    return ROMANIZATION_ALIASES.get(text, text)


def _cp_int(cp: str) -> int | None:
    if not cp.startswith("U+"):
        return None
    try:
        return int(cp[2:], 16)
    except ValueError:
        return None


def prefer_pure_final(romanization: str, cp: str, role: str | None) -> bool:
    """Disambiguate bare i/y/u: final header / final role → 以/厶/无; else onset 云/危."""
    r = normalize_romanization(romanization)
    if r not in _AMBIGUOUS_ONSET_FINALS:
        return r in FINAL_HAN and r not in INITIAL_MARKER

    role_l = (role or "").lower()
    if "initial" in role_l and "final" not in role_l:
        return False
    if "final" in role_l and "initial" not in role_l:
        return True

    code = _cp_int(cp)
    if code is not None and code in _FINAL_HEADER_RANGE:
        return True
    return False


def split_romanization(
    romanization: str, *, cp: str = "", role: str | None = None
) -> tuple[str | None, str | None]:
    """Return (initial, final). final is '' for bare initial; both None if unknown."""
    r = normalize_romanization(romanization)
    if not r:
        return None, None

    # Pure final (no initial): header slots like a, aq, … and ambiguous i/y/u there.
    if r in FINAL_HAN and prefer_pure_final(r, cp, role):
        return "", r

    for initial in _INITIALS_SORTED:
        if r == initial:
            return initial, ""
        if r.startswith(initial):
            rest = r[len(initial) :]
            if rest in FINAL_HAN:
                return initial, rest
            if rest == "":
                return initial, ""
            continue

    # Non-ambiguous pure finals (a, aq, …) if not caught above.
    if r in FINAL_HAN:
        return "", r

    return None, None


def expected_chinese(
    romanization: str, *, cp: str = "", role: str | None = None
) -> str | None:
    """Return expected Chinese hint, or None if no rule applies."""
    if cp in SPECIAL_BY_CODEPOINT:
        return SPECIAL_BY_CODEPOINT[cp]

    raw = (romanization or "").strip()
    if raw in SPECIAL_BY_ROMANIZATION:
        return SPECIAL_BY_ROMANIZATION[raw]

    # After alias normalize, bare "-" already handled; also catch normalized zero.
    norm = normalize_romanization(raw)
    if norm in SPECIAL_BY_ROMANIZATION:
        return SPECIAL_BY_ROMANIZATION[norm]

    initial, final = split_romanization(romanization, cp=cp, role=role)
    if initial is None or final is None:
        return None
    if initial == "":
        return FINAL_HAN[final]
    marker = INITIAL_MARKER.get(initial)
    if marker is None:
        return None
    if final == "":
        return marker
    return marker + FINAL_HAN[final]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def process(
    data: dict,
) -> tuple[dict, list[tuple[str, str, str, str]], int, int, int, list[tuple[str, str]]]:
    """Return (out, mismatches, filled_count, already_ok, skipped_empty_rom, unfilled)."""
    out = copy.deepcopy(data)
    glyphs: dict[str, dict] = out["glyphs"]
    mismatches: list[tuple[str, str, str, str]] = []
    filled = 0
    already_ok = 0
    skipped_empty_rom = 0
    unfilled: list[tuple[str, str]] = []

    for cp, entry in glyphs.items():
        if not isinstance(entry, dict):
            continue
        raw_rom = (entry.get("romanization") or "").strip()
        current = (entry.get(CHINESE_KEY) or "").strip()

        if not raw_rom:
            skipped_empty_rom += 1
            continue

        role = entry.get("role")
        expected = expected_chinese(raw_rom, cp=cp, role=role if isinstance(role, str) else None)
        if expected is None:
            if not current:
                unfilled.append((cp, raw_rom))
            continue

        if current:
            if current == expected:
                already_ok += 1
            else:
                mismatches.append((cp, raw_rom, current, expected))
            continue

        entry[CHINESE_KEY] = expected
        filled += 1

    return out, mismatches, filled, already_ok, skipped_empty_rom, unfilled


def write_report(
    path: Path,
    *,
    filled: int,
    already_ok: int,
    skipped_empty_rom: int,
    mismatches: list[tuple[str, str, str, str]],
    unfilled: list[tuple[str, str]],
    input_path: Path,
    output_path: Path,
) -> None:
    lines = [
        "# Chinese orthography validation report",
        "",
        f"- Input: `{input_path.relative_to(ROOT)}`",
        f"- Output: `{output_path.relative_to(ROOT)}`",
        f"- Newly filled empty fields: **{filled}**",
        f"- Already filled and matching rules: **{already_ok}**",
        f"- Mismatches (handfill ≠ rule): **{len(mismatches)}**",
        f"- Entries with romanization but no rule / still empty: **{len(unfilled)}**",
        f"- Entries with empty romanization (skipped): **{skipped_empty_rom}**",
        "",
        "## Mismatches",
        "",
    ]
    if not mismatches:
        lines.append("_None._")
    else:
        lines.append("| codepoint | romanization | handfill | expected |")
        lines.append("| --- | --- | --- | --- |")
        for cp, rom, got, exp in mismatches:
            lines.append(f"| {cp} | `{rom}` | {got} | {exp} |")

    lines.extend(["", "## Unfilled (no rule)", ""])
    if not unfilled:
        lines.append("_None._")
    else:
        lines.append("| codepoint | romanization |")
        lines.append("| --- | --- |")
        for cp, rom in unfilled:
            lines.append(f"| {cp} | `{rom}` |")

    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    data = load_json(args.input)
    out, mismatches, filled, already_ok, skipped, unfilled = process(data)
    write_json(args.output, out)
    write_report(
        args.report,
        filled=filled,
        already_ok=already_ok,
        skipped_empty_rom=skipped,
        mismatches=mismatches,
        unfilled=unfilled,
        input_path=args.input.resolve(),
        output_path=args.output.resolve(),
    )
    print(
        f"filled={filled} ok={already_ok} mismatches={len(mismatches)} "
        f"unfilled={len(unfilled)} -> {args.output}"
    )


if __name__ == "__main__":
    main()
