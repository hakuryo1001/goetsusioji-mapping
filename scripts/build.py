#!/usr/bin/env python3
"""Build mapping/goetsusioji.json from the hand-edited handfill source.

Canonical Siauzy: head block is always a grid glyph (U+F040–U+F4F9);
beside blocks are header-row finals/codas (U+F021–U+F03B) only where the
chart rules place a part beside the head. Never emit loose U+F5xx pieces as
syllable blocks. Exception: null-onset bare finals may carry a separate
`letter` field (chart-2 U+F5xx final glyph) for the typer to prefer first.
Han spelling is the progenitor-hanzi string for every syllable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDFILL_PATH = ROOT / "handfilling" / "glyphs-handfill-with-chinese.json"
OUT_PATH = ROOT / "mapping" / "goetsusioji.json"
FONT_CANDIDATES = [
    ROOT / "goetsusioji.ttf",
    ROOT.parent / "goetsusioji-reference" / "goetsusioji.ttf",
]

CHINESE_KEY = "chinese character only orthography"
GRID_RANGE = range(0xF040, 0xF4FA)
HEADER_RANGE = range(0xF021, 0xF040)
COMPONENT_RANGE = range(0xF500, 0xF546)

ROM_ALIASES = {
    "ch(i)": "ch",
    "c(i)": "c",
    "j(i)": "j",
    "sh(i)": "sh",
    "zh(i)": "zh",
    "ae(n)": "ae",
    "oe(n)": "oe",
    "ie(n)": "ie",
    "mh | m": "mh",
    "zero | null": "zero",
    "hn": "-n",
    "hq": "-q",
}

OPEN_FINALS_FOR_CODA = [
    "a", "o", "e", "i", "u", "au", "ou", "eu", "iu",
    "ae", "oe", "ie", "en", "an", "on", "eon", "in", "y", "aon", "r",
]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def cp_int(cp: str) -> int:
    return int(cp.replace("U+", ""), 16)


def cp_key(code: int) -> str:
    return f"U+{code:04X}"


def norm_rom(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    if text in ROM_ALIASES:
        return ROM_ALIASES[text]
    if " | " in text:
        text = text.split(" | ", 1)[0].strip()
    return ROM_ALIASES.get(text, text)


def find_font() -> Path | None:
    for path in FONT_CANDIDATES:
        if path.exists():
            return path
    return None


def load_font_codepoints() -> set[int] | None:
    font_path = find_font()
    if font_path is None:
        return None
    from fontTools.ttLib import TTFont

    font = TTFont(str(font_path))
    cmap = font.getBestCmap() or {}
    return set(cmap)


class Builder:
    def __init__(self, handfill: dict) -> None:
        self.glyphs: dict[str, dict] = handfill["glyphs"]
        self.chart: dict = handfill["chart"]
        self.grid: dict[str, tuple[str, str]] = {}  # rom -> (cp, char)
        self.header: dict[str, tuple[str, str]] = {}  # rom -> (cp, char)
        self.comp_by_rom: dict[str, tuple[str, str, str]] = {}  # rom -> (cp, char, role)
        self._index_glyphs()

        self.initials_order = [i["key"] for i in self.chart["initials"]]
        self.finals_order = [f["key"] for f in self.chart["finals"]]
        self.medial_keys = [m["key"] for m in self.chart["medials"]]
        self.implicit_i = set(self.chart["implicit_i_initials"])
        self.compound_finals = dict(self.chart["compound_finals"])
        self.coda_attachments = dict(self.chart.get("coda_attachments", {}))
        # Merge chart-2 attachments into compound table for enumeration.
        for key, parts in self.coda_attachments.items():
            self.compound_finals.setdefault(key, parts)

        self.initial_meta = {i["key"]: i for i in self.chart["initials"]}
        self.medial_meta = {m["key"]: m for m in self.chart["medials"]}
        self.coda_meta = {c["key"]: c for c in self.chart["codas"]}

        self.han_initial = self._build_han_initials()
        self.han_final = self._build_han_finals()
        self.han_coda = {c["key"]: c["han"] for c in self.chart["codas"]}
        self.han_medial = {m["key"]: m["han"] for m in self.chart["medials"]}

    def _index_glyphs(self) -> None:
        for cp, entry in self.glyphs.items():
            code = cp_int(cp)
            rom = norm_rom(entry.get("romanization") or "")
            char = entry.get("char") or ""
            if not rom or not char:
                continue
            if code in GRID_RANGE:
                col = code & 0x1F
                rank = 0 if col >= 1 else 1
                prev = self.grid.get(rom)
                if prev is None or rank < (0 if (cp_int(prev[0]) & 0x1F) >= 1 else 1):
                    self.grid[rom] = (cp, char)
                elif rank == 0 and prev is not None and (cp_int(prev[0]) & 0x1F) >= 1:
                    if code < cp_int(prev[0]):
                        self.grid[rom] = (cp, char)
            if code in HEADER_RANGE:
                self.header[rom] = (cp, char)
                # Also index coda keys with leading hyphen.
                if rom in ("q", "n"):
                    self.header[f"-{rom}"] = (cp, char)
            if code in COMPONENT_RANGE:
                role = entry.get("role") or ""
                prev = self.comp_by_rom.get(rom)
                # Prefer a dedicated initial slot over final/medial when roms collide (i, u).
                if prev is None:
                    self.comp_by_rom[rom] = (cp, char, role)
                else:
                    prev_role = prev[2] or ""
                    if "initial" in role and "initial" not in prev_role:
                        self.comp_by_rom[rom] = (cp, char, role)
                    elif "initial" in prev_role:
                        pass
                    elif "final" in role and "final" not in prev_role:
                        self.comp_by_rom[rom] = (cp, char, role)

    def _han_at(self, cp: str) -> str:
        return (self.glyphs.get(cp, {}).get(CHINESE_KEY) or "").strip()

    def _build_han_initials(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for key in self.initials_order:
            # Prefer component slot Han (initial role).
            for rom_try in (key, "zero | null" if key in ("zero", "null") else key):
                hit = self.comp_by_rom.get(rom_try)
                if not hit:
                    continue
                role = hit[2] or ""
                ok = "initial" in role or (
                    key in ("zero", "null") and hit[0] == "U+F50F"
                )
                if not ok:
                    continue
                han = self._han_at(hit[0])
                if han:
                    out[key] = han
                    break
            if key in out:
                continue
            # Grid col-0 header for this initial.
            for rom_try in (key, "-"):
                if rom_try in self.grid and (cp_int(self.grid[rom_try][0]) & 0x1F) == 0:
                    han = self._han_at(self.grid[rom_try][0])
                    if han:
                        out[key] = han
                        break
            if key not in out:
                group = self.initial_meta.get(key, {}).get("group", "")
                out[key] = group
        for key in ("null", "zero"):
            out.setdefault(key, "奧")
        # Glide onsets: empty grid-col Han should not stick as 奧.
        for key, fallback in (("i", "云"), ("y", "云"), ("u", "危"), ("w", "危")):
            if out.get(key) in ("", "奧"):
                out[key] = fallback
        return out

    def _build_han_finals(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for key in self.finals_order:
            for store in (self.header, self.comp_by_rom):
                hit = store.get(key) or store.get(f"{key}(n)")
                if not hit:
                    continue
                cp = hit[0]
                han = self._han_at(cp)
                if han:
                    out[key] = han
                    break
            out.setdefault(key, "")
        return out

    def onset_grid_key(self, initial: str) -> str:
        """Prefix used in grid romanizations for this initial."""
        if initial in ("null", "zero"):
            return "-"
        return initial

    def typed_rom(self, initial: str, body: str) -> str:
        """Romanization the typer accepts (no null/zero prefix)."""
        if initial in ("null", "zero"):
            return body
        return initial + body

    def grid_lookup(self, key: str) -> tuple[str, str] | None:
        return self.grid.get(key)

    def beside_lookup(self, key: str) -> tuple[str, str] | None:
        """Header-row glyph for a beside final/coda."""
        if key in self.header:
            return self.header[key]
        # Component hn/hq → coda
        if key in ("-n", "-q") and key in self.header:
            return self.header[key]
        return None

    def han_parts(
        self,
        initial: str | None,
        medial: str | None,
        final: str | None,
        coda: str | None,
        final_parts: list[str] | None = None,
    ) -> str:
        chunks: list[str] = []
        if initial and initial not in ("null", "zero"):
            chunks.append(self.han_initial.get(initial, ""))
        elif initial in ("null", "zero"):
            chunks.append(self.han_initial.get(initial, "奧"))
        if medial:
            chunks.append(self.han_medial.get(medial, self.han_final.get(medial, "")))
        if final_parts:
            for part in final_parts:
                if part.startswith("-"):
                    chunks.append(self.han_coda.get(part, ""))
                else:
                    chunks.append(self.han_final.get(part, ""))
        elif final:
            chunks.append(self.han_final.get(final, ""))
        if coda:
            chunks.append(self.han_coda.get(coda, ""))
        return "".join(chunks)

    def make_entry(
        self,
        *,
        romanization: str,
        rule: int,
        parts: dict,
        head_key: str,
        beside_keys: list[str],
        han: str,
    ) -> dict:
        blocks: list[dict] = []
        missing: str | None = None

        head = self.grid_lookup(head_key)
        if head is None:
            missing = f"no grid glyph for head block {head_key!r}"
        else:
            covers = ["initial"]
            if parts.get("medial"):
                covers.append("medial")
            if parts.get("final") and not beside_keys:
                covers.append("final")
            elif parts.get("final_parts"):
                covers.append("final_part_1")
            elif parts.get("final") and beside_keys:
                # Head is initial(+medial); final is beside — or head is initial+part1.
                if rule in (2,) or (
                    rule == 4 and parts.get("medial")
                ):
                    pass  # head covers initial+medial only
                else:
                    covers.append("final_part_1" if parts.get("final_parts") else "final")
            blocks.append(
                {
                    "codepoint": head[0],
                    "covers": covers,
                    "position": "head",
                }
            )

        for i, bkey in enumerate(beside_keys):
            beside = self.beside_lookup(bkey)
            if beside is None:
                missing = missing or f"no header glyph for beside {bkey!r}"
                continue
            if parts.get("final_parts") and i < len(parts["final_parts"]) - (
                0 if parts.get("medial") and rule == 4 else 0
            ):
                cover = (
                    ["final_part_2"]
                    if bkey.startswith("-") or bkey in ("i",) and "final_parts" in parts
                    else ["final"]
                )
                if bkey.startswith("-"):
                    cover = ["coda"] if parts.get("coda") or bkey in ("-q", "-n") else ["final_part_2"]
                elif parts.get("final_parts"):
                    # map to which part
                    fps = parts["final_parts"]
                    if bkey == fps[-1] or (bkey == "i" and "i" in fps):
                        cover = ["final_part_2"]
                    else:
                        cover = ["final_part_1"]
                else:
                    cover = ["final"]
            else:
                if bkey.startswith("-"):
                    cover = ["coda"]
                else:
                    cover = ["final"]
            blocks.append(
                {
                    "codepoint": beside[0],
                    "covers": cover,
                    "position": "beside",
                }
            )

        if missing:
            return {
                "rule": rule,
                "parts": parts,
                "goetsu": None,
                "blocks": [],
                "missing": missing,
                "han": han,
            }

        goetsu = "".join(self.glyphs[b["codepoint"]]["char"] for b in blocks)
        # Single head block: hand-entered grid Han wins when present.
        if len(blocks) == 1:
            hand_han = self._han_at(blocks[0]["codepoint"])
            if hand_han:
                han = hand_han
        return {
            "rule": rule,
            "parts": parts,
            "goetsu": goetsu,
            "blocks": blocks,
            "han": han,
        }

    def make_letter_variant(self, final: str) -> dict | None:
        """Chart-2 raw final letter (U+F5xx) for empty-onset bare finals."""
        hit = self.comp_by_rom.get(final)
        if not hit:
            return None
        cp, char, _role = hit
        if cp_int(cp) not in COMPONENT_RANGE or not char:
            return None
        han = self.han_final.get(final) or self._han_at(cp) or ""
        return {
            "goetsu": char,
            "han": han,
            "blocks": [
                {
                    "codepoint": cp,
                    "covers": ["final"],
                    "position": "letter",
                }
            ],
        }


def build_components(builder: Builder) -> dict:
    initials: dict[str, dict] = {}
    for key in builder.initials_order:
        onset = builder.onset_grid_key(key)
        cp = None
        glyph = None
        # Prefer U+F5xx component
        for rom in (key, "zero | null" if key in ("null", "zero") else None, "-"):
            if rom is None:
                continue
            hit = builder.comp_by_rom.get(rom)
            if hit and (
                "initial" in (hit[2] or "")
                or (key in ("null", "zero") and hit[0] == "U+F50F")
                or (key == "mh" and rom == "mh")
            ):
                cp, glyph = hit[0], hit[1]
                break
        if cp is None and onset in builder.grid:
            cp, glyph = builder.grid[onset]
        initials[key] = {
            "codepoint": cp,
            "glyph": glyph,
            "han": builder.han_initial.get(key, ""),
            "group": builder.initial_meta.get(key, {}).get("group", ""),
        }

    finals: dict[str, dict] = {}
    for key in builder.finals_order:
        hit = builder.comp_by_rom.get(key) or (
            builder.header[key] + ("",) if key in builder.header else None
        )
        if key in builder.comp_by_rom:
            cp, glyph, _ = builder.comp_by_rom[key]
        elif key in builder.header:
            cp, glyph = builder.header[key]
        else:
            cp, glyph = None, None
        finals[key] = {
            "codepoint": cp,
            "glyph": glyph,
            "han": builder.han_final.get(key, ""),
        }

    medials: dict[str, dict] = {}
    for key in builder.medial_keys:
        # Prefer final|medial component, else header/final.
        cp, glyph = None, None
        for rom, (c, ch, role) in builder.comp_by_rom.items():
            if norm_rom(rom) == key and "medial" in (role or ""):
                cp, glyph = c, ch
                break
        if cp is None:
            if key in builder.comp_by_rom:
                cp, glyph = builder.comp_by_rom[key][0], builder.comp_by_rom[key][1]
            elif key in builder.header:
                cp, glyph = builder.header[key]
        medials[key] = {
            "codepoint": cp,
            "glyph": glyph,
            "han": builder.han_medial.get(key, ""),
            "label": builder.medial_meta.get(key, {}).get("label", ""),
        }

    codas: dict[str, dict] = {}
    for key in ("-q", "-n"):
        hit = builder.beside_lookup(key)
        codas[key] = {
            "codepoint": hit[0] if hit else None,
            "glyph": hit[1] if hit else None,
            "han": builder.han_coda.get(key, ""),
        }

    return {
        "initials": initials,
        "finals": finals,
        "medials": medials,
        "codas": codas,
    }


def build_rules(chart: dict) -> list[dict]:
    return [
        {
            "id": 1,
            "name": "simple",
            "layout": {"top": "initial", "bottom": "final"},
            "zh": "聲母符號和韻母符號拼合起來就可以表達一個字音，拼寫時聲母在上，韻母在下。",
            "example": {"romanization": "keq", "hanzi": "個"},
        },
        {
            "id": 2,
            "name": "with_medial",
            "layout": {"top": "initial", "below": "medial", "beside": "final"},
            "zh": "拼寫時聲母在上，介母在其下，韻母在介母之右。",
            "example": {"romanization": "tiau", "hanzi": "鳥"},
        },
        {
            "id": 3,
            "name": "implicit_i",
            "layout": {"top": "initial", "bottom": "final"},
            "zh": "ch(i)、c(i)、j(i) 和 sh(i)、zh(i) 視為已含介母 i，因此不用再標出介音 i。",
            "example": {"romanization": "shian", "hanzi": "向"},
            "implicit_i_initials": chart["implicit_i_initials"],
        },
        {
            "id": 4,
            "name": "compound_final",
            "layout": {"top": "initial", "bottom": "final_part_1", "beside": "final_part_2"},
            "zh": "aeq、oeq、eoq、ai、ei 等有專門寫法（下+右布局），同時按照介音字的方式進行拼寫。",
            "example": {"romanization": "maeq", "hanzi": "襪"},
            "compound_finals": chart["compound_finals"],
        },
        {
            "id": 5,
            "name": "yu",
            "layout": {"top": "initial", "bottom": "final"},
            "zh": "由於目前撮口音 iu 基本上不區分尖團，所以不再單獨設立 yu 韻母；如需表記，用 y+u（grid yu）。",
            "example": {"romanization": "yu", "hanzi": None},
        },
    ]


def enumerate_syllables(builder: Builder) -> tuple[dict[str, dict], dict[str, str], dict]:
    syllables: dict[str, dict] = {}
    aliases: dict[str, str] = {}
    stats = {
        "with_goetsu": 0,
        "missing_goetsu": 0,
        "simple": 0,
        "implicit_i": 0,
        "with_medial": 0,
        "compound": 0,
        "compound_medial": 0,
        "bound_coda": 0,
        "skipped_duplicate": 0,
        "letter_variants": 0,
    }

    def put(rom: str, entry: dict, bucket: str) -> None:
        if rom in syllables or rom in aliases:
            stats["skipped_duplicate"] += 1
            return
        syllables[rom] = entry
        stats[bucket] += 1
        if entry.get("goetsu"):
            stats["with_goetsu"] += 1
        else:
            stats["missing_goetsu"] += 1

    initials = builder.initials_order
    # Emit zero-onset once (null and zero share the same grid row).
    # Put null last so bare roms like "ie"/"iu" prefer glide-initial rows
    # (i+e, i+u) over zero-onset + final when both exist in the font grid.
    onset_initials = [i for i in initials if i not in ("zero", "null")] + ["null"]
    finals = builder.finals_order
    medials = builder.medial_keys
    compounds = list(builder.compound_finals.keys())

    # Rule 1: simple
    for ini in onset_initials:
        prefix = builder.onset_grid_key(ini)
        for fin in finals:
            body = fin
            rom = builder.typed_rom(ini, body)
            head_key = f"{prefix}{fin}" if prefix != "-" else f"-{fin}"
            # Grid uses '-a' form for zero onset.
            if prefix == "-":
                head_key = f"-{fin}"
            else:
                head_key = f"{prefix}{fin}"
            # Special: grid loanword r under zero is '-hr'
            if prefix == "-" and fin == "r":
                head_key = "-hr"
            han = builder.han_parts(ini, None, fin, None)
            put(
                rom,
                builder.make_entry(
                    romanization=rom,
                    rule=1,
                    parts={
                        "initial": ini if ini not in ("null",) else "null",
                        "medial": None,
                        "final": fin,
                        "coda": None,
                    },
                    head_key=head_key,
                    beside_keys=[],
                    han=han,
                ),
                "simple",
            )

    # Rule 3: implicit-i spellings (shian etc.), head = shan block.
    # Skip finals that already begin with i (ie, iu, in, …) — inserting another
    # i would invent bogus keys like chiie and collide with real chie.
    for ini in builder.implicit_i:
        for fin in finals:
            if fin == "i" or fin.startswith("i"):
                continue
            rom = ini + "i" + fin
            compact = ini + fin
            head_key = compact
            han = builder.han_parts(ini, None, fin, None)
            put(
                rom,
                builder.make_entry(
                    romanization=rom,
                    rule=3,
                    parts={
                        "initial": ini,
                        "medial": None,
                        "final": fin,
                        "coda": None,
                        "implicit_i": True,
                    },
                    head_key=head_key,
                    beside_keys=[],
                    han=han,
                ),
                "implicit_i",
            )
            # Alias compact→full only when they are the same written syllable
            # (shan/shian share the shan block). Never drop distinct che vs chie.
            if compact != rom and compact in syllables and rom in syllables:
                if (
                    syllables[compact].get("goetsu")
                    and syllables[compact].get("goetsu") == syllables[rom].get("goetsu")
                ):
                    del syllables[compact]
                    aliases[compact] = rom

    # Rule 2: with medial
    for ini in onset_initials:
        if ini in builder.implicit_i:
            medials_use = [m for m in medials if m != "i"]
        else:
            medials_use = medials
        prefix = builder.onset_grid_key(ini)
        for med in medials_use:
            head_key = f"{prefix}{med}" if prefix != "-" else f"-{med}"
            if prefix == "-":
                head_key = f"-{med}"
            else:
                head_key = f"{ini}{med}"
            for fin in finals:
                body = med + fin
                rom = builder.typed_rom(ini, body)
                han = builder.han_parts(ini, med, fin, None)
                put(
                    rom,
                    builder.make_entry(
                        romanization=rom,
                        rule=2,
                        parts={
                            "initial": ini,
                            "medial": med,
                            "final": fin,
                            "coda": None,
                        },
                        head_key=head_key,
                        beside_keys=[fin],
                        han=han,
                    ),
                    "with_medial",
                )

    # Rule 4 + coda attachments as compound finals
    for ini in onset_initials:
        prefix = builder.onset_grid_key(ini)
        for compound, parts in builder.compound_finals.items():
            body = compound
            rom = builder.typed_rom(ini, body)
            part1, part2 = parts[0], parts[1]
            if prefix == "-":
                head_key = f"-{part1}"
                if part1 == "r":
                    head_key = "-hr"
            else:
                head_key = f"{ini}{part1}"
            han = builder.han_parts(ini, None, None, None, final_parts=parts)
            put(
                rom,
                builder.make_entry(
                    romanization=rom,
                    rule=4,
                    parts={
                        "initial": ini,
                        "medial": None,
                        "final": compound,
                        "final_parts": parts,
                        "coda": part2 if part2.startswith("-") else None,
                    },
                    head_key=head_key,
                    beside_keys=[part2],
                    han=han,
                ),
                "compound",
            )

    # Rule 4 with medial
    for ini in onset_initials:
        if ini in builder.implicit_i:
            medials_use = [m for m in medials if m != "i"]
        else:
            medials_use = medials
        for med in medials_use:
            head_key = f"{ini}{med}" if ini not in ("null", "zero") else f"-{med}"
            for compound, parts in builder.compound_finals.items():
                body = med + compound
                rom = builder.typed_rom(ini, body)
                han = builder.han_parts(ini, med, None, None, final_parts=parts)
                put(
                    rom,
                    builder.make_entry(
                        romanization=rom,
                        rule=4,
                        parts={
                            "initial": ini,
                            "medial": med,
                            "final": compound,
                            "final_parts": parts,
                            "coda": parts[1] if parts[1].startswith("-") else None,
                        },
                        head_key=head_key,
                        beside_keys=list(parts),
                        han=han,
                    ),
                    "compound_medial",
                )

    # Bound coda on open finals: baen = ban + -n, bauq = bau + -q
    for ini in onset_initials:
        prefix = builder.onset_grid_key(ini)
        for fin in OPEN_FINALS_FOR_CODA:
            for coda in ("-q", "-n"):
                suffix = coda.removeprefix("-")
                body = fin + suffix
                rom = builder.typed_rom(ini, body)
                if prefix == "-":
                    head_key = f"-{fin}" if fin != "r" else "-hr"
                else:
                    head_key = f"{ini}{fin}"
                # Skip if already created as a compound (e.g. aeq, aoq).
                if rom in syllables:
                    continue
                han = builder.han_parts(ini, None, fin, coda)
                put(
                    rom,
                    builder.make_entry(
                        romanization=rom,
                        rule=1,
                        parts={
                            "initial": ini,
                            "medial": None,
                            "final": fin,
                            "coda": coda,
                        },
                        head_key=head_key,
                        beside_keys=[coda],
                        han=han,
                    ),
                    "bound_coda",
                )

    # Bound coda on medial syllables
    for ini in onset_initials:
        if ini in builder.implicit_i:
            medials_use = [m for m in medials if m != "i"]
        else:
            medials_use = medials
        for med in medials_use:
            head_key = f"{ini}{med}" if ini not in ("null", "zero") else f"-{med}"
            for fin in OPEN_FINALS_FOR_CODA:
                for coda in ("-q", "-n"):
                    suffix = coda.removeprefix("-")
                    body = med + fin + suffix
                    rom = builder.typed_rom(ini, body)
                    if rom in syllables:
                        continue
                    han = builder.han_parts(ini, med, fin, coda)
                    put(
                        rom,
                        builder.make_entry(
                            romanization=rom,
                            rule=2,
                            parts={
                                "initial": ini,
                                "medial": med,
                                "final": fin,
                                "coda": coda,
                            },
                            head_key=head_key,
                            beside_keys=[fin, coda],
                            han=han,
                        ),
                        "bound_coda",
                    )

    # Grammar marker tsy
    for gm in builder.chart.get("grammar_markers", []):
        key = gm["key"]
        cp = gm.get("codepoint")
        if not cp or key in syllables:
            continue
        char = builder.glyphs.get(cp, {}).get("char", "")
        han = builder._han_at(cp) or builder.han_parts("ts", None, "y", None)
        if char and cp_int(cp) in GRID_RANGE:
            syllables[key] = {
                "rule": 1,
                "parts": {"initial": "ts", "medial": None, "final": "y", "coda": None},
                "goetsu": char,
                "blocks": [
                    {"codepoint": cp, "covers": ["initial", "final"], "position": "head"}
                ],
                "han": han or "子厶",
                "grammar": True,
            }
            stats["simple"] += 1
            stats["with_goetsu"] += 1

    # Empty-onset bare finals: attach chart-2 letter so the typer can prefer it.
    letter_count = 0
    for rom, entry in syllables.items():
        parts = entry.get("parts") or {}
        if parts.get("initial") != "null":
            continue
        fin = parts.get("final")
        if not fin or fin != rom:
            continue
        if parts.get("medial") or parts.get("coda") or parts.get("final_parts"):
            continue
        letter = builder.make_letter_variant(fin)
        if not letter:
            continue
        entry["letter"] = letter
        letter_count += 1
    stats["letter_variants"] = letter_count

    return syllables, aliases, stats


def validate(
    mapping: dict,
    builder: Builder,
    font_cps: set[int] | None,
) -> list[str]:
    errors: list[str] = []
    syllables = mapping["syllables"]

    for rom, entry in syllables.items():
        goetsu = entry.get("goetsu")
        blocks = entry.get("blocks") or []
        if goetsu is not None:
            if not blocks:
                errors.append(f"{rom}: goetsu set but no blocks")
            else:
                head = blocks[0]
                if head.get("position") != "head":
                    errors.append(f"{rom}: first block is not head")
                head_cp = cp_int(head["codepoint"])
                if head_cp not in GRID_RANGE:
                    errors.append(f"{rom}: head {head['codepoint']} not in grid range")
                for b in blocks[1:]:
                    if b.get("position") != "beside":
                        errors.append(f"{rom}: non-beside block {b}")
                    bcp = cp_int(b["codepoint"])
                    if bcp not in HEADER_RANGE:
                        errors.append(
                            f"{rom}: beside {b['codepoint']} not in header range (loose component?)"
                        )
                    if bcp in COMPONENT_RANGE:
                        errors.append(f"{rom}: loose component piece {b['codepoint']}")
                if font_cps is not None:
                    for b in blocks:
                        if cp_int(b["codepoint"]) not in font_cps:
                            errors.append(f"{rom}: {b['codepoint']} missing from font")

                # Recompute goetsu from blocks
                recomputed = "".join(
                    builder.glyphs[b["codepoint"]]["char"] for b in blocks
                )
                if recomputed != goetsu:
                    errors.append(f"{rom}: goetsu mismatch vs blocks")

        letter = entry.get("letter")
        if letter:
            l_goetsu = letter.get("goetsu")
            l_blocks = letter.get("blocks") or []
            if not l_goetsu:
                errors.append(f"{rom}: letter missing goetsu")
            elif not l_blocks:
                errors.append(f"{rom}: letter goetsu set but no blocks")
            else:
                for b in l_blocks:
                    if b.get("position") != "letter":
                        errors.append(f"{rom}: letter block position {b.get('position')!r}")
                    bcp = cp_int(b["codepoint"])
                    if bcp not in COMPONENT_RANGE:
                        errors.append(
                            f"{rom}: letter {b['codepoint']} not in component range"
                        )
                    if font_cps is not None and bcp not in font_cps:
                        errors.append(f"{rom}: letter {b['codepoint']} missing from font")
                recomputed = "".join(
                    builder.glyphs[b["codepoint"]]["char"] for b in l_blocks
                )
                if recomputed != l_goetsu:
                    errors.append(f"{rom}: letter goetsu mismatch vs blocks")

    # Chart examples
    expect = {
        "keq": {"rule": 1, "han_contains": "工出"},
        "tiau": {"rule": 2},
        "shian": {"rule": 3},
        "maeq": {"rule": 4},
        "aoq": {},
        "iuq": {},
        "yu": {},
    }
    for rom, exp in expect.items():
        entry = syllables.get(rom)
        if entry is None:
            errors.append(f"chart example {rom}: missing")
            continue
        if "rule" in exp and entry.get("rule") != exp["rule"]:
            errors.append(
                f"chart example {rom}: rule {entry.get('rule')} != {exp['rule']}"
            )
        if "han_contains" in exp and exp["han_contains"] not in (entry.get("han") or ""):
            errors.append(
                f"chart example {rom}: han {entry.get('han')!r} missing {exp['han_contains']}"
            )
        if rom in ("keq", "tiau", "shian", "maeq", "yu") and not entry.get("goetsu"):
            errors.append(f"chart example {rom}: missing goetsu ({entry.get('missing')})")

    # Single-block syllables must surface the handfill Han when the cell has one.
    for rom, entry in syllables.items():
        blocks = entry.get("blocks") or []
        if len(blocks) != 1 or not entry.get("goetsu"):
            continue
        hand_han = (builder.glyphs.get(blocks[0]["codepoint"], {}).get(CHINESE_KEY) or "").strip()
        if hand_han and entry.get("han") != hand_han:
            errors.append(
                f"han mismatch {rom}: entry={entry.get('han')!r} handfill={hand_han!r}"
            )

    return errors


def build() -> dict:
    handfill = load_json(HANDFILL_PATH)
    if "chart" not in handfill:
        raise SystemExit("handfill missing chart section; migrate source first")
    builder = Builder(handfill)
    components = build_components(builder)
    rules = build_rules(builder.chart)
    syllables, aliases, stats = enumerate_syllables(builder)

    # Prefer shian over shan as canonical; alias shan→shian already set.
    # If both exist with same goetsu, keep both keys but alias compact→full for implicit.

    tones = [
        {
            "category": t.get("category", t.get("key")),
            "mark": t.get("mark"),
            "key": t.get("key"),
            "note": t.get("note"),
        }
        for t in builder.chart["tones"]
    ]

    mapping = {
        "meta": {
            "description": (
                "Canonical Goetsusioji mapping: romanization → Siauzy glyph blocks "
                "+ progenitor Han spelling. Generated from handfill; do not hand-edit."
            ),
            "generated_by": "scripts/build.py",
            "source": str(HANDFILL_PATH.relative_to(ROOT)),
            "syllable_count": len(syllables),
            "stats": stats,
            "decisions": builder.chart.get("decisions", {}),
        },
        "components": components,
        "rules": rules,
        "tones": tones,
        "initials_order": [
            i for i in builder.initials_order if i != "zero"
        ],
        "finals_order": builder.finals_order,
        "medials_order": builder.medial_keys,
        "syllables": dict(sorted(syllables.items())),
        "aliases": dict(sorted(aliases.items())),
    }
    return mapping, builder


def cmd_build(args: argparse.Namespace) -> int:
    mapping, builder = build()
    font_cps = load_font_codepoints()
    errors = validate(mapping, builder, font_cps)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
        f.write("\n")

    stats = mapping["meta"]["stats"]
    print(f"Wrote {OUT_PATH}")
    print(f"  syllables: {mapping['meta']['syllable_count']}")
    print(f"  with_goetsu: {stats['with_goetsu']}")
    print(f"  missing_goetsu: {stats['missing_goetsu']}")
    print(f"  aliases: {len(mapping['aliases'])}")
    if font_cps is None:
        print("  warning: font not found; skipped font codepoint checks")

    samples = ["keq", "ba", "tiau", "shian", "shan", "maeq", "aoq", "iuq", "yu", "baen", "a", "e"]
    for s in samples:
        key = mapping["aliases"].get(s, s)
        e = mapping["syllables"].get(key)
        if not e:
            print(f"  {s}: MISSING")
            continue
        g = e.get("goetsu")
        letter = e.get("letter")
        letter_bit = (
            f" letter={letter.get('goetsu')!r}/{letter.get('han')!r}"
            if letter
            else ""
        )
        print(
            f"  {s}: goetsu={g!r} han={e.get('han')!r} rule={e.get('rule')} "
            f"missing={e.get('missing')}{letter_bit}"
        )

    missing = [r for r, e in mapping["syllables"].items() if not e.get("goetsu")]
    print(f"  null goetsu count: {len(missing)}")
    if args.show_missing:
        for r in missing[:80]:
            print(f"    {r}: {mapping['syllables'][r].get('missing')}")
        if len(missing) > 80:
            print(f"    ... and {len(missing) - 80} more")

    if errors:
        print(f"VALIDATION FAILED ({len(errors)} errors):")
        for err in errors[:60]:
            print(f"  - {err}")
        if len(errors) > 60:
            print(f"  ... and {len(errors) - 60} more")
        return 1
    print("Validation OK")
    return 0


def cmd_lookup(args: argparse.Namespace) -> int:
    if not OUT_PATH.exists():
        print(f"Missing {OUT_PATH}; run build first", file=sys.stderr)
        return 1
    mapping = load_json(OUT_PATH)
    for rom in args.romanizations:
        key = rom.strip().lower()
        key = mapping.get("aliases", {}).get(key, key)
        entry = mapping["syllables"].get(key)
        if not entry:
            print(f"{rom}: not found")
            continue
        print(json.dumps({rom: entry}, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd")

    p_build = sub.add_parser("build", help="Regenerate mapping/goetsusioji.json")
    p_build.add_argument(
        "--show-missing",
        action="store_true",
        help="Print syllables with null goetsu",
    )
    p_build.set_defaults(func=cmd_build)

    p_lookup = sub.add_parser("lookup", help="Look up romanizations in the mapping")
    p_lookup.add_argument("romanizations", nargs="+")
    p_lookup.set_defaults(func=cmd_lookup)

    # Default to build when no subcommand.
    args = parser.parse_args(argv)
    if args.cmd is None:
        args = parser.parse_args(["build"] + (argv or []))
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
