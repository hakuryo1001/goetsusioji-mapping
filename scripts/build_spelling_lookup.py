#!/usr/bin/env python3
"""Build data/spelling-lookup.json — {romanization, char} with fused glyphs where available."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDFILL_PATH = ROOT / "data" / "glyphs-handfill-with-chinese.json"
SPELLING_PATH = ROOT / "data" / "spelling-compose-rules.json"
MANIFEST_PATH = ROOT / "data" / "chart-manifest.json"
OUT_PATH = ROOT / "data/spelling-lookup.json"

SYLLABLE_GRID = range(0xF040, 0xF4FA)
CODA_ONLY = {"-q", "-n"}

DIALECT_FINALS: dict[str, list[str]] = {
    "aoq": ["a", "o", "-q"],
    "iuq": ["iu", "-q"],
}

OPEN_FINALS_FOR_CODA = [
    "a", "o", "e", "i", "u", "au", "ou", "eu", "iu",
    "ae", "oe", "ie", "en", "an", "on", "eon", "in", "y", "aon", "r",
]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_fused_glyphs(handfill: dict) -> dict[str, str]:
    """Romanization → fused syllable char from the font grid (U+F040..F4F9)."""
    hits: dict[str, tuple[int, str]] = {}
    for cp_key, entry in handfill["glyphs"].items():
        cp = int(cp_key.replace("U+", ""), 16)
        if cp not in SYLLABLE_GRID:
            continue
        rom = (entry.get("romanization") or "").strip()
        char = entry.get("char") or ""
        if not rom or not char:
            continue
        col = cp & 0x1F
        # Prefer real syllable cells (col >= 1) over col-0 initial-only headers.
        rank = 0 if col >= 1 else 1
        prev = hits.get(rom)
        if prev is None or (rank, cp) < (prev[0], int(cp_key.replace("U+", ""), 16)):
            hits[rom] = (rank, char)
    return {rom: char for rom, (_, char) in hits.items()}


class SpellingBuilder:
    def __init__(self, spelling: dict, manifest: dict, fused: dict[str, str]) -> None:
        self.fused = fused
        self.initials = spelling["components"]["initials"]
        self.finals = spelling["components"]["finals"]
        self.medials = spelling["components"]["medials"]
        self.initials_order = spelling["initials_order"]
        self.finals_order = [
            f["key"] for f in manifest["finals"] if f["key"] not in CODA_ONLY
        ]
        self.medial_keys = [m["key"] for m in manifest["medials"]]
        self.implicit_i_initials = set(spelling["implicit_i_initials"])
        self.compound_finals = dict(manifest["compose"]["compound_finals"])
        self.compound_finals.update(DIALECT_FINALS)

    def _comp(self, key: str, *, prefer: str | None = None) -> str | None:
        order: list[dict]
        if prefer == "medial":
            order = [self.medials, self.initials, self.finals]
        elif prefer == "initial":
            order = [self.initials, self.finals, self.medials]
        elif prefer == "final":
            order = [self.finals, self.medials, self.initials]
        else:
            order = [self.initials, self.finals, self.medials]
        for pool in order:
            hit = pool.get(key)
            if hit:
                return hit["char"]
        return None

    def _join(self, *keys: str, roles: list[str] | None = None) -> str | None:
        chars: list[str] = []
        for i, key in enumerate(keys):
            prefer = roles[i] if roles and i < len(roles) else None
            ch = self._comp(key, prefer=prefer)
            if not ch:
                return None
            chars.append(ch)
        return "".join(chars)

    def fused_or_components(self, romanization: str, *component_keys: str) -> str | None:
        """Use fused grid glyph when the whole string exists; else component join."""
        if romanization in self.fused:
            return self.fused[romanization]
        return self._join(*component_keys)

    def fused_prefix_plus_components(
        self, romanization: str, prefix_rom: str, *suffix_keys: str
    ) -> str | None:
        """Prefer fused prefix + component suffix (e.g. phae + -q)."""
        prefix = self.fused.get(prefix_rom)
        suffix = self._join(*suffix_keys)
        if prefix and suffix:
            return prefix + suffix
        ini = ""
        for key in self.initials_order:
            if romanization.startswith(key):
                if len(key) > len(ini):
                    ini = key
        if not ini:
            return None
        rest = romanization[len(ini) :]
        return self.fused_or_components(romanization, ini, *self._split_rest(rest))

    def _split_rest(self, rest: str) -> list[str]:
        for compound in sorted(self.compound_finals, key=len, reverse=True):
            if rest == compound:
                return self.compound_finals[compound]
        for fin in sorted(self.finals_order, key=len, reverse=True):
            if rest == fin:
                return [fin]
        return list(rest)

    def simple(self, initial: str, final: str) -> dict | None:
        rom = initial + final
        char = self.fused_or_components(rom, initial, final)
        if not char:
            return None
        return {"romanization": rom, "char": char}

    def implicit_i(self, initial: str, final: str) -> dict | None:
        rom = initial + ("i" if final == "i" else "i" + final)
        # Do not map shian → fused shan; romanizations differ.
        char = self.fused.get(rom) or self._join(initial, final)
        if not char:
            return None
        return {"romanization": rom, "char": char}

    def with_medial(self, initial: str, medial: str, final: str) -> dict | None:
        rom = initial + medial + final
        if rom in self.fused:
            return {"romanization": rom, "char": self.fused[rom]}
        char = self._join(initial, medial, final, roles=["initial", "medial", "final"])
        if not char:
            return None
        return {"romanization": rom, "char": char}

    def compound(self, initial: str, compound_key: str) -> dict | None:
        rom = initial + compound_key
        if rom in self.fused:
            return {"romanization": rom, "char": self.fused[rom]}
        parts = self.compound_finals[compound_key]
        if len(parts) == 2:
            stem = initial + parts[0]
            char = self.fused_prefix_plus_components(rom, stem, parts[1])
            if char:
                return {"romanization": rom, "char": char}
        char = self._join(initial, *parts, roles=["initial"] + ["final"] * len(parts))
        if not char:
            return None
        return {"romanization": rom, "char": char}

    def compound_medial(self, initial: str, medial: str, compound_key: str) -> dict | None:
        rom = initial + medial + compound_key
        if rom in self.fused:
            return {"romanization": rom, "char": self.fused[rom]}
        parts = self.compound_finals[compound_key]
        roles = ["initial", "medial"] + ["final"] * len(parts)
        char = self._join(initial, medial, *parts, roles=roles)
        if not char:
            return None
        return {"romanization": rom, "char": char}

    def bound_coda(self, initial: str, final: str, coda: str) -> dict | None:
        suffix = coda.removeprefix("-")
        rom = initial + final + suffix
        if rom in self.fused:
            return {"romanization": rom, "char": self.fused[rom]}
        stem = initial + final
        char = self.fused_prefix_plus_components(rom, stem, coda)
        if not char:
            char = self._join(initial, final, coda)
        if not char:
            return None
        return {"romanization": rom, "char": char}


def build() -> dict:
    handfill = load_json(HANDFILL_PATH)
    spelling = load_json(SPELLING_PATH)
    manifest = load_json(MANIFEST_PATH)
    fused = load_fused_glyphs(handfill)
    builder = SpellingBuilder(spelling, manifest, fused)

    by_rom: dict[str, str] = {}
    stats = {
        "fused_whole": 0,
        "simple": 0,
        "implicit_i": 0,
        "with_medial": 0,
        "compound": 0,
        "compound_medial": 0,
        "bound_coda": 0,
        "skipped": 0,
    }

    def put(entry: dict | None, bucket: str) -> None:
        if not entry:
            stats["skipped"] += 1
            return
        rom, char = entry["romanization"], entry["char"]
        if rom in by_rom:
            return
        by_rom[rom] = char
        stats[bucket] += 1
        if rom in fused and char == fused[rom]:
            stats["fused_whole"] += 1

    initials = builder.initials_order
    finals = builder.finals_order
    medials = builder.medial_keys
    compounds = list(builder.compound_finals.keys())
    implicit = [i for i in initials if i in builder.implicit_i_initials]

    for ini in initials:
        for fin in finals:
            put(builder.simple(ini, fin), "simple")

    for ini in implicit:
        for fin in finals:
            if fin == "i":
                continue
            put(builder.implicit_i(ini, fin), "implicit_i")

    for ini in initials:
        for med in medials:
            if ini in builder.implicit_i_initials and med == "i":
                continue
            for fin in finals:
                put(builder.with_medial(ini, med, fin), "with_medial")

    for ini in initials:
        for compound in compounds:
            put(builder.compound(ini, compound), "compound")

    for ini in initials:
        for med in medials:
            if ini in builder.implicit_i_initials and med == "i":
                continue
            for compound in compounds:
                put(builder.compound_medial(ini, med, compound), "compound_medial")

    for ini in initials:
        for fin in OPEN_FINALS_FOR_CODA:
            for coda in ("-q", "-n"):
                put(builder.bound_coda(ini, fin, coda), "bound_coda")

    spellings = [{"romanization": rom, "char": char} for rom, char in sorted(by_rom.items())]

    return {
        "meta": {
            "description": (
                "Romanization → Goetsusioji char. Uses fused syllable glyphs from "
                "glyphs-handfill-with-chinese.json (U+F040..F4F9) when available; "
                "only splits into components for medials, compound finals, bound "
                "codas, and other chart-3 exceptions."
            ),
            "generated_by": "scripts/build_spelling_lookup.py",
            "count": len(spellings),
            "fused_glyph_count": len(fused),
            "stats": stats,
        },
        "spellings": spellings,
    }


def main() -> int:
    out = build()
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    handfill = load_json(HANDFILL_PATH)
    fused = load_fused_glyphs(handfill)
    lookup = {s["romanization"]: s["char"] for s in out["spellings"]}

    print(f"Wrote {OUT_PATH}")
    print(f"  count: {out['meta']['count']}")
    print(f"  fused_whole: {out['meta']['stats']['fused_whole']}")
    samples = ["bi", "keq", "ba", "tiau", "shian", "shan", "maeq", "phaeq", "baoq", "bauq", "bann"]
    for s in samples:
        ch = lookup.get(s, "MISSING")
        tag = "fused" if s in fused and ch == fused[s] else f"len={len(ch) if ch != 'MISSING' else 0}"
        print(f"  {s}: {repr(ch)} ({tag})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
