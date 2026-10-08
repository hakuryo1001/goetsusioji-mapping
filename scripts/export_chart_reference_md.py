#!/usr/bin/env python3
"""Export docs/goetsu-xiaozi-charts.md from handfill JSON + chart structure.

Faithful readable replica of pics/1.png, pics/2.png, pics/3.png with Goetsu PUA
glyphs and Chinese origins. Re-run after handfill glyph updates.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDFILL = ROOT / "handfilling" / "glyphs-handfill-with-chinese.json"
MAPPING = ROOT / "mapping" / "goetsusioji.json"
OUTPUT = ROOT / "docs" / "goetsu-xiaozi-charts.md"


def load_glyphs() -> dict[str, dict]:
    with HANDFILL.open(encoding="utf-8") as f:
        return json.load(f)["glyphs"]


def load_mapping() -> dict:
    if not MAPPING.exists():
        return {}
    with MAPPING.open(encoding="utf-8") as f:
        return json.load(f)


def index_by_rom(glyphs: dict[str, dict]) -> dict[str, list[tuple[str, dict]]]:
    out: dict[str, list[tuple[str, dict]]] = {}
    for cp, entry in glyphs.items():
        rom = (entry.get("romanization") or "").strip()
        if not rom:
            continue
        out.setdefault(rom, []).append((cp, entry))
    return out


_ROM_ALIASES = {
    "mh": "mh | m",
    "m": "mh | m",
    "zero": "zero | null",
    "-": "zero | null",
}


def pick(
    by_rom: dict[str, list[tuple[str, dict]]],
    rom: str,
    *,
    prefer_role: str | None = None,
    prefer_cp_prefix: str | None = None,
) -> tuple[str, str] | None:
    """Return (codepoint, char) or None."""
    candidates = [rom]
    if rom in _ROM_ALIASES:
        candidates.append(_ROM_ALIASES[rom])
    if " | " in rom:
        candidates.append(rom.split(" | ", 1)[0].strip())

    hits: list[tuple[str, dict]] = []
    for key in candidates:
        hits.extend(by_rom.get(key, []))
    # de-dupe by codepoint, keep order
    seen: set[str] = set()
    uniq: list[tuple[str, dict]] = []
    for cp, e in hits:
        if cp in seen:
            continue
        seen.add(cp)
        uniq.append((cp, e))
    hits = uniq
    if not hits:
        return None

    if prefer_role:
        role_hits = [
            (cp, e)
            for cp, e in hits
            if prefer_role in (e.get("role") or "")
        ]
        if role_hits:
            hits = role_hits

    if prefer_cp_prefix:
        pref = [h for h in hits if h[0].startswith(prefer_cp_prefix)]
        if pref:
            hits = pref

    f5 = [h for h in hits if h[0] >= "U+F500"]
    if f5:
        hits = f5

    # Prefer lower codepoint within remaining (stable chart order)
    hits = sorted(hits, key=lambda h: h[0])
    cp, entry = hits[0]
    return cp, entry.get("char") or ""

def cell(rom: str, char: str, cp: str, origin: str, notes: str = "") -> str:
    g = char if char else "—"
    c = cp if cp else "—"
    n = notes if notes else "—"
    return f"| `{rom}` | {g} | {origin} | `{c}` | {n} |"


def empty_row(label: str = "*(empty)*") -> str:
    return f"| {label} | — | — | — | — |"


def build_md(glyphs: dict[str, dict]) -> str:
    by_rom = index_by_rom(glyphs)
    lines: list[str] = []

    def g(
        rom: str,
        *,
        role: str | None = None,
        prefix: str | None = None,
    ) -> tuple[str, str]:
        hit = pick(by_rom, rom, prefer_role=role, prefer_cp_prefix=prefix)
        if hit:
            return hit
        return ("", "")

    lines.extend(
        [
            "# 吳小字（Goetsu Xiaozi）— Chart Reference",
            "",
            "Faithful, maximal-detail readable replica of the three reference charts.",
            "",
            "| Chart | Source image |",
            "| --- | --- |",
            "| 聲母表 | [`pics/1.png`](../pics/1.png) |",
            "| 韻母表 | [`pics/2.png`](../pics/2.png) |",
            "| 介母 · 聲調 · 拼寫規則 | [`pics/3.png`](../pics/3.png) |",
            "",
            "## How to read this document",
            "",
            "- **Goetsu glyph** columns use Private Use Area characters from the Goetsusioji font.",
            "  Install/configure the font per [`.vscode/font-setup.md`](../.vscode/font-setup.md).",
            "  Without that font you will see empty boxes or fallback tofu.",
            "- **Chinese origin** is the chart’s example / group Han character (what the red glyph is derived from).",
            "- **Codepoint** is the mapped PUA slot in [`handfilling/glyphs-handfill-with-chinese.json`](../handfilling/glyphs-handfill-with-chinese.json).",
            "  Chart-1 initials/finals prefer `U+F500`… where available; syllable-grid duplicates may also exist.",
            "- This file is a **human-readable chart**. Hand-edited source: `handfilling/`.",
            "  Canonical typer table: [`mapping/goetsusioji.json`](../mapping/goetsusioji.json) (from `python3 scripts/build.py`).",
            "- **Siauzy** is always canonical font glyphs (never CSS-stacked).",
            "  **Han** is the progenitor-hanzi spelling (man'yōgana-style teaching layer).",
            "",
            "### Chart vs Han-spelling conventions",
            "",
            "| Topic | On these charts | In Han spelling |",
            "| --- | --- | --- |",
            "| Final `y` | **私（空韻）** | **厶** |",
            "| Final `oq` | **昱** | **昱** |",
            "| Fricatives `f` / `s` / `sh` | Pic 1 draws **゜** on the Goetsu glyphs | Unmarked 弗 / 式 / 兴 |",
            "| `h` | **゜** on glyph | 奧ﾟ |",
            "",
            "---",
            "",
            "# Chart 1 — 聲母表 (Initials)",
            "",
            "## Introductory text (left panel)",
            "",
            "**吳小字**",
            "",
            "吳小字是標音文字，由上下部件拼合而成。其部件包括聲母符號、韻母符號（含介母）和聲調符號。",
            "（通常文句中因連續變調，多只標變調而不標本調。）",
            "",
            "聲母符號共有 **16** 個，清一色。在符號右上方加 **半濁符號「゜」** 表示送氣；",
            "加 **濁音符號「〃」**（手寫常作「'」）表示全濁。",
            "",
            "另外，**l、m、n、ny、ng** 五個聲母預設為濁（陽／下）；加半濁符號「゜」表示清（陰／上）。",
            "",
            "共 **33（+5）** 個聲母符號。",
            "",
            "*English:* Goetsu Xiaozi is a phonemic script built from stacked components",
            "(initial + final/medial + optional tone). Sixteen basic voiceless initials;",
            "゜ marks aspiration (or yin sonorants); 〃 marks full voicing.",
            "",
            "## Initial groups (right panel)",
            "",
            "Each row is an **initial-only** glyph (no final). Layout follows the chart’s group blocks.",
            "Diacritic notes describe what pic 1 shows on the red glyph.",
            "",
        ]
    )

    # --- Pic 1 groups ---
    initial_groups: list[tuple[str, list[tuple[str, str, str]]]] = [
        # (group Han, [(rom, diacritic_note, origin_override?)])
        (
            "兵",
            [
                ("ph", "aspirated ゜", "兵"),
                ("p", "plain", "兵"),
                ("b", "voiced 〃", "兵"),
            ],
        ),
        (
            "弗",
            [
                ("f", "chart shows ゜ on glyph", "弗"),
                ("v", "voiced 〃", "弗"),
            ],
        ),
        (
            "矛",
            [
                ("mh", "yin/clear ゜ on sonorant", "矛"),
                ("m", "default yang sonorant", "矛"),
            ],
        ),
        (
            "刀",
            [
                ("th", "aspirated ゜", "刀"),
                ("t", "plain", "刀"),
                ("d", "voiced 〃", "刀"),
            ],
        ),
        (
            "力",
            [
                ("lh", "yin/clear ゜", "力"),
                ("l", "default yang sonorant", "力"),
            ],
        ),
        (
            "斤",
            [
                ("ch(i)", "aspirated ゜; implicit medial i", "斤"),
                ("c(i)", "plain; implicit medial i", "斤"),
                ("j(i)", "voiced 〃; implicit medial i", "斤"),
            ],
        ),
        (
            "兴",
            [
                ("sh(i)", "chart shows ゜; implicit medial i", "兴"),
                ("zh(i)", "voiced 〃; implicit medial i", "兴"),
            ],
        ),
        (
            "拿",
            [
                ("nh", "yin/clear ゜", "拿"),
                ("n", "default yang sonorant", "拿"),
            ],
        ),
        (
            "子",
            [
                ("tsh", "aspirated ゜", "子"),
                ("ts", "plain", "子"),
                ("dz", "voiced 〃", "子"),
            ],
        ),
        (
            "式",
            [
                ("s", "chart shows ゜ on glyph", "式"),
                ("z", "voiced 〃", "式"),
            ],
        ),
        (
            "女",
            [
                ("nyh", "yin/clear ゜", "女"),
                ("ny", "default yang sonorant", "女"),
            ],
        ),
        (
            "工",
            [
                ("kh", "aspirated ゜", "工"),
                ("k", "plain", "工"),
                ("g", "voiced 〃", "工"),
            ],
        ),
        (
            "奥",
            [
                ("h", "chart shows ゜ on glyph", "奥"),
                ("…", "blank / null onset cell under 奥 (shares zero glyph)", "奥"),
                ("gh", "voiced 〃", "奥"),
            ],
        ),
        (
            "午",
            [
                ("nk", "yin/clear ゜", "午"),
                ("ng", "default yang sonorant", "午"),
            ],
        ),
        (
            "零聲母",
            [
                ("zero | null", "zero initial (chart label …)", "零聲母"),
            ],
        ),
        (
            "云",
            [
                ("i", "onset / medial-related; chart pair with y", "云"),
                ("y", "onset; chart pair with i", "云"),
            ],
        ),
        (
            "危",
            [
                ("u", "onset u / glide", "危"),
                ("w", "onset w", "危"),
            ],
        ),
    ]

    lines.extend(
        [
            "| Group | Romanization | Goetsu glyph | Chinese origin | Codepoint | Notes |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )

    for group, rows in initial_groups:
        for i, (rom, note, origin) in enumerate(rows):
            if rom == "…":
                # blank under 奥 — same glyph as zero
                cp, char = g("zero | null", role="initial")
                if not cp:
                    cp, char = g("-")
                group_cell = group if i == 0 else ""
                lines.append(
                    f"| {group_cell} | `…` | {char or '—'} | {origin} | `{cp or '—'}` | {note} |"
                )
                continue
            cp, char = g(rom, role="initial")
            if not cp:
                # syllable-grid bare initial
                alt = rom.replace("(i)", "")
                if " | " in rom:
                    alt = rom.split(" | ", 1)[0]
                cp, char = g(alt)
                if not cp and rom == "zero | null":
                    cp, char = g("-")
            group_cell = group if i == 0 else ""
            lines.append(
                f"| {group_cell} | `{rom}` | {char or '—'} | {origin} | `{cp or '—'}` | {note} |"
            )

    lines.extend(
        [
            "",
            "### Chart-1 initial components (PUA `U+F500`…), same order as export",
            "",
            "| Codepoint | Romanization | Goetsu glyph | Role |",
            "| --- | --- | --- | --- |",
        ]
    )
    for cp in sorted(k for k in glyphs if k >= "U+F500" and k <= "U+F545"):
        e = glyphs[cp]
        role = e.get("role") or ""
        if "initial" not in role:
            continue
        rom = e.get("romanization") or ""
        lines.append(f"| `{cp}` | `{rom}` | {e.get('char') or '—'} | {role} |")

    # --- Pic 2 ---
    lines.extend(
        [
            "",
            "---",
            "",
            "# Chart 2 — 韻母表 (Finals)",
            "",
            "## Introductory text (top panel)",
            "",
            "基本韻母符號 **24** 個，韻尾符號 **2** 個：促音韻尾 **く（-q）** 和兒化韻尾 **レ（-n）**，",
            "可以用後加的方式來表述具體語境或習慣說法中的臨時音變以及個別地區的特殊韻母。",
            "例如：**aoq（ㄈく）**、**iuq（ミく）**。",
            "",
            "此外還有 **1** 個專用符號 **（ㄞ）**，用來表示外來音中 **l/r** 韻尾。總計 **27** 個韻母符號。",
            "",
            "*English:* 24 basic finals + 2 coda attachments (-q checked, -n er/nasal) + 1 loanword r/l final = 27.",
            "",
            "## Finals grid",
            "",
            "Each cell on the chart: **romanization** (top-left) · **Goetsu glyph** (red) · **example Han** (bottom).",
            "",
            "| Romanization | Goetsu glyph | Chinese origin (chart) | Codepoint | Notes |",
            "| --- | --- | --- | --- | --- |",
        ]
    )

    finals_grid: list[tuple[str, str, str] | None] = [
        # rom, origin as on chart, notes
        ("a", "派", ""),
        ("o", "瓦", ""),
        ("e", "卑", ""),
        ("i", "以", "also medial 齊齒呼"),
        ("u", "无", "also medial 合口呼"),
        ("au", "号", ""),
        ("ou", "多", ""),
        ("eu", "久", ""),
        ("iu", "雨", "also medial 撮口呼"),
        None,  # empty
        ("aq", "乏", ""),
        ("oq", "昱", "chart origin 昱"),
        ("eq", "出", ""),
        ("iq", "亦", ""),
        ("q", "促化/塞韻尾", "coda **-q**; glyph く-family"),
        ("ae(n)", "万", "ae / ae(n)"),
        ("oe(n)", "寒", "oe / oe(n)"),
        ("en", "文", ""),
        ("ie(n)", "建", "ie / ie(n)"),
        ("n", "兒化/鼻韻尾", "coda **-n**; glyph レ"),
        ("an", "良", ""),
        ("on", "从", ""),
        ("eon", "能", ""),
        ("in", "刃", ""),
        ("y", "私（空韻）", "chart 私; handfill Chinese hint often 厶"),
        ("aon", "亡", ""),
        None,
        None,
        None,
        ("r", "而", "loanword l/r; dedicated ㄞ"),
    ]

    for item in finals_grid:
        if item is None:
            lines.append(empty_row())
            continue
        rom, origin, notes = item
        # Prefer header-range finals U+F021.. for basic grid; components for q/n in F03x
        if rom in ("q", "n"):
            cp, char = g(rom, prefix="U+F03")
        elif rom in ("ae(n)", "oe(n)", "ie(n)"):
            cp, char = g(rom, role="final")
            if not cp:
                base = rom.split("(")[0]
                cp, char = g(base, prefix="U+F02")
        else:
            cp, char = g(rom, prefix="U+F02")
            if not cp:
                cp, char = g(rom, role="final")
            if not cp:
                cp, char = g(rom)
        lines.append(cell(rom, char, cp, origin, notes))

    lines.extend(
        [
            "",
            "### Chart-2 / component finals (`role` contains final)",
            "",
            "| Codepoint | Romanization | Goetsu glyph | Role |",
            "| --- | --- | --- | --- |",
        ]
    )
    for cp in sorted(k for k in glyphs if k >= "U+F521" and k <= "U+F53B"):
        e = glyphs[cp]
        role = e.get("role") or ""
        if "final" not in role:
            continue
        rom = e.get("romanization") or ""
        lines.append(f"| `{cp}` | `{rom}` | {e.get('char') or '—'} | {role} |")

    # --- Pic 3 ---
    lines.extend(
        [
            "",
            "---",
            "",
            "# Chart 3 — 介母 · 聲調 · 拼寫規則",
            "",
            "## 介母表 (Medials)",
            "",
            "介母符號 **3** 個；另外 1 個翹舌介母 **而（r）**，供部分地區殘留翹舌與外來詞使用。",
            "",
            "| Romanization | Goetsu glyph | Chinese label (chart) | Codepoint | Notes |",
            "| --- | --- | --- | --- | --- |",
        ]
    )

    medials = [
        ("i", "以（齊齒呼）", "final | medial"),
        ("u", "无（合口呼）", "final | medial"),
        ("iu", "雨（撮口呼）", "final | medial"),
        ("r", "而（翹舌）", "final | medial"),
    ]
    for rom, label, role in medials:
        cp, char = g(rom, role=role)
        if not cp:
            cp, char = g(rom, prefix="U+F02")
        lines.append(cell(rom, char, cp, label, role))

    lines.extend(
        [
            "",
            "## 聲調表 (Tones)",
            "",
            "聲調符號 **4** 個；變調符號 **3** 個。聲調分陰陽，**由聲母的清濁決定**。",
            "因連續變調，句中單字本調通常不必標出。",
            "",
            "| Category | Mark (romanization) | Chart symbol | Notes |",
            "| --- | --- | --- | --- |",
            "| 平 (level) | `-` (often unmarked) | horizontal dash | Yin/Yang by initial voicing |",
            "| 上 (rising) | `'` / ´ | rising stroke | |",
            "| 去 (departing) | `` ` `` / `ˋ` | falling stroke | |",
            "| 入 (entering) | `-q` | `<` | expressed via checked final |",
            "| 變調 | `-x` | dash | sandhi |",
            "| 變調 | `-·` | middle dot `·` | sandhi |",
            "",
            "## 拼寫規則 (Spelling rules)",
            "",
            "### 1. 一般字音 — initial above final",
            "",
            "聲母在上，韻母在下。",
            "",
            "| Syllable | Chart Han | Siauzy | Codepoint(s) | Han spelling | Decomposition |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )

    mapping = load_mapping()
    syllables = mapping.get("syllables") or {}
    aliases = mapping.get("aliases") or {}

    def composed_row(syll: str, chart_han: str, decomp: str) -> str:
        key = aliases.get(syll, syll)
        entry = syllables.get(key)
        if entry and entry.get("goetsu"):
            blocks = entry.get("blocks") or []
            cps = ", ".join(f"`{b['codepoint']}`" for b in blocks) or "—"
            han = entry.get("han") or "—"
            return (
                f"| `{syll}` | {chart_han} | {entry['goetsu']} | {cps} | "
                f"{han} | {decomp} |"
            )
        missing = (entry or {}).get("missing") or "not in mapping"
        return (
            f"| `{syll}` | {chart_han} | — | — | "
            f"{(entry or {}).get('han') or '—'} | {decomp} ({missing}) |"
        )

    lines.append(composed_row("keq", "個", "k + eq"))

    # component lookup for decomposition display
    def show_parts(*roms: str) -> str:
        parts = []
        for r in roms:
            got = pick(by_rom, r, prefer_role="initial") or pick(
                by_rom, r, prefer_role="final"
            ) or pick(by_rom, r)
            if got:
                parts.append(f"`{r}`={got[1]} (`{got[0]}`)")
            else:
                parts.append(f"`{r}`=*(missing)*")
        return "; ".join(parts)

    lines.extend(
        [
            "",
            f"Component glyphs: {show_parts('k', 'eq')}",
            "",
            "### 2. 含介母字音 — initial + medial + final",
            "",
            "聲母在上；介母在聲母之下；韻母在介母之右。",
            "",
            "| Syllable | Chart Han | Siauzy | Codepoint(s) | Han spelling | Decomposition |",
            "| --- | --- | --- | --- | --- | --- |",
            composed_row("tiau", "鳥", "ti head + au beside"),
            "",
            f"Component glyphs: {show_parts('t', 'i', 'au')}",
            "",
            "### 3. 隱含介母 i — ch(i)/c(i)/j(i)、sh(i)/zh(i)",
            "",
            "斤組、兴組聲母視為已含介母 i，不再另寫介母「以」。",
            "",
            "| Syllable | Chart Han | Siauzy | Codepoint(s) | Han spelling | Decomposition |",
            "| --- | --- | --- | --- | --- | --- |",
            composed_row("shian", "向", "shan head block (alias shan→shian)"),
            "",
            f"Component glyphs: {show_parts('sh(i)', 'an')}",
            "",
            "### 4. 方言韻母 — aeq / oeq / eoq / ai / ei",
            "",
            "地方韻母可用「下 + 右」拼合（與介母布局類似）。",
            "Chart notes forms such as aeq、oeq、eoq 與 ai、ei。",
            "",
            "| Syllable | Chart Han | Siauzy | Codepoint(s) | Han spelling | Notes |",
            "| --- | --- | --- | --- | --- | --- |",
            composed_row("maeq", "襪", "mae head + -q beside"),
            composed_row("aeq", "—", "ae + -q"),
            composed_row("oeq", "—", "oe + -q"),
            composed_row("eoq", "—", "eon + -q"),
            composed_row("ai", "—", "a + i"),
            composed_row("ei", "—", "e + i"),
            "",
            "### 5. 撮口介母 iu",
            "",
            "撮口介母 iu 一般不另立 yu 韻；尖團多已合流。需要時用 grid `yu`（y+u）。",
            "",
            "| Syllable | Chart Han | Siauzy | Codepoint(s) | Han spelling | Notes |",
            "| --- | --- | --- | --- | --- | --- |",
            composed_row("yu", "—", "y-initial + u-final grid block"),
            "",
            f"Medial `iu` glyph: {show_parts('iu')}",
            "",
            "---",
            "",
            "## Maintenance",
            "",
            "Regenerate the canonical mapping, then this file:",
            "",
            "```bash",
            "python3 scripts/build.py",
            "python3 scripts/export_chart_reference_md.py",
            "```",
            "",
            "Glyphs come from `handfilling/glyphs-handfill-with-chinese.json`;",
            "rule examples pull Siauzy/Han from `mapping/goetsusioji.json`.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    glyphs = load_glyphs()
    md = build_md(glyphs)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(md, encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
