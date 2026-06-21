#!/usr/bin/env python3
"""Parse hand-curated component glyphs from data/chart-tables-handfill.md."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDFILL_PATH = ROOT / "data" / "chart-tables-handfill.md"

PUA_RE = re.compile(r"[\uF021-\uF545]")
CP_RE = re.compile(r"U\+([0-9A-Fa-f]{4})")

ROMANIZE_ALIASES = {
    "ch(i)": "ch",
    "c(i)": "c",
    "j(i)": "j",
    "sh(i)": "sh",
    "zh(i)": "zh",
    "ae(n)": "ae",
    "oe(n)": "oe",
    "ie(n)": "ie",
}


def cp_str(cp: int) -> str:
    return f"U+{cp:04X}"


def char_str(cp: int) -> str:
    return chr(cp)


def normalize_romanization(raw: str) -> str | None:
    text = raw.strip().strip("*").lower()
    if not text or text.startswith("(") or text in {"name"}:
        return None
    return ROMANIZE_ALIASES.get(text, text)


def extract_codepoint(glyph: str, codepoint_col: str) -> int | None:
    for col in (codepoint_col, glyph):
        if not col:
            continue
        for match in CP_RE.finditer(col):
            cp = int(match.group(1), 16)
            if 0xF021 <= cp <= 0xF545:
                return cp
    for col in (glyph, codepoint_col):
        if not col:
            continue
        pua = PUA_RE.findall(col)
        if pua:
            return ord(pua[0])
    return None


def parse_table_rows(section: str) -> list[tuple[str, str, str, str]]:
    """Return (romanization, glyph, codepoint_col, group)."""
    rows: list[tuple[str, str, str, str]] = []
    current_group = ""
    header: list[str] = []
    for line in section.splitlines():
        if line.startswith("#### "):
            current_group = line.removeprefix("#### ").strip()
            header = []
            continue
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) < 2:
            continue
        if parts[0].lower() in {"romanization", "name", "syllable", "expected syllable"}:
            header = [p.lower() for p in parts]
            continue
        if set(parts[0]) <= {"-", " "}:
            continue

        glyph = parts[1] if len(parts) > 1 else ""
        codepoint_col = ""
        if header:
            if "codepoint" in header:
                codepoint_col = parts[header.index("codepoint")]
            elif "example hanzi" in header and "codepoint" not in header:
                # finals table without codepoint column filled
                codepoint_col = parts[header.index("codepoint")] if "codepoint" in header else ""
        if not codepoint_col and len(parts) > 2:
            # Section 1: romanization | glyph | codepoint | notes
            # Section 2/3: codepoint is column index 3 when present
            if len(parts) >= 4 and parts[3].upper().startswith("U+"):
                codepoint_col = parts[3]
            elif len(parts) == 3 or (len(parts) >= 3 and not parts[2][:1].isascii()):
                codepoint_col = parts[2] if parts[2].upper().startswith("U+") else ""
            else:
                codepoint_col = parts[2] if parts[2].upper().startswith("U+") else ""

        rows.append((parts[0], glyph, codepoint_col, current_group))
    return rows


def parse_handfill(path: Path = HANDFILL_PATH) -> dict:
    text = path.read_text(encoding="utf-8")
    s1 = text.find("# Section 1")
    s2 = text.find("# Section 2")
    s3 = text.find("# Section 3")
    if min(s1, s2, s3) < 0:
        raise ValueError("handfill file missing expected section headers")

    initials: dict[str, dict] = {}
    finals: dict[str, dict] = {}
    medials: dict[str, dict] = {}
    warnings: list[str] = []

    for romanization, glyph, codepoint_col, group in parse_table_rows(text[s1:s2]):
        key = normalize_romanization(romanization)
        if key is None:
            continue
        if key == "…":
            key = "zero" if group == "零聲母" else "null" if group == "奥" else None
            if key is None:
                warnings.append(f"ambiguous ellipsis in group {group!r}")
                continue
        cp = extract_codepoint(glyph, codepoint_col)
        if cp is None:
            warnings.append(f"missing initial glyph: {key} ({group})")
            continue
        initials[key] = {
            "codepoint": cp_str(cp),
            "char": char_str(cp),
            "group": group,
            "source": "chart-tables-handfill.md#section-1",
        }

    for romanization, glyph, codepoint_col, group in parse_table_rows(text[s2:s3]):
        key = normalize_romanization(romanization)
        if key is None:
            continue
        cp = extract_codepoint(glyph, codepoint_col)
        if cp is None:
            warnings.append(f"missing final glyph: {key}")
            continue
        finals[key] = {
            "codepoint": cp_str(cp),
            "char": char_str(cp),
            "group": group or "finals-grid",
            "source": "chart-tables-handfill.md#section-2",
        }

    for romanization, glyph, codepoint_col, _group in parse_table_rows(
        text[s3 : text.find("## 3.1")]
    ):
        key = normalize_romanization(romanization)
        if key is None:
            continue
        cp = extract_codepoint(glyph, codepoint_col)
        if cp is None:
            warnings.append(f"missing medial glyph: {key}")
            continue
        medials[key] = {
            "codepoint": cp_str(cp),
            "char": char_str(cp),
            "source": "chart-tables-handfill.md#section-3",
        }

    return {"initials": initials, "finals": finals, "medials": medials, "warnings": warnings}
