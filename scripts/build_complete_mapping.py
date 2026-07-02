#!/usr/bin/env python3
"""Build data/complete-mapping.json — every syllable spelling → component glyph sequence."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPELLING_PATH = ROOT / "data" / "spelling-compose-rules.json"
MANIFEST_PATH = ROOT / "data" / "chart-manifest.json"
GRID_PATH = ROOT / "mapping" / "goetsuese-mapping.json"
OUT_PATH = ROOT / "data" / "complete-mapping.json"

# Grid finals usable as syllable rimes (exclude bound coda components).
CODA_ONLY = {"-q", "-n"}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def glyph_ref(comp: dict | None, slot: str, role: str, key: str) -> dict | None:
    if comp is None:
        return None
    return {
        "slot": slot,
        "role": role,
        "key": key,
        "codepoint": comp["codepoint"],
        "char": comp["char"],
    }


def compose_entry(
    *,
    romanization: str,
    parse: dict,
    layout: str,
    rule: int,
    slots: dict[str, dict | None],
    slot_order: list[str],
    precomposed: dict | None = None,
) -> dict | None:
    glyphs = []
    for slot in slot_order:
        role_key = {
            "top": ("initial", parse.get("initial")),
            "bottom": ("final", parse.get("final_part_1") or parse.get("final")),
            "bottom_left": ("medial", parse.get("medial")),
            "right": ("final", parse.get("final")),
            "right_bottom": ("final_part_1", parse.get("final_part_1")),
            "right_top": ("final_part_2", parse.get("final_part_2")),
        }.get(slot, (slot, None))
        role, key = role_key
        if slot in ("bottom", "right_bottom") and parse.get("compound"):
            key = parse.get("final_parts", [None, None])[0]
        if slot in ("right", "right_top") and parse.get("compound"):
            parts = parse.get("final_parts", [None, None])
            key = parts[1] if len(parts) > 1 else parse.get("final")
        g = glyph_ref(slots.get(slot), slot, role, key or "")
        if g is None:
            return None
        glyphs.append(g)

    entry = {
        "romanization": romanization,
        "parse": parse,
        "layout": layout,
        "rule": rule,
        "glyphs": glyphs,
        "glyph_string": "".join(g["char"] for g in glyphs),
        "codepoints": [g["codepoint"] for g in glyphs],
    }
    if precomposed:
        entry["precomposed"] = precomposed
    return entry


class Composer:
    def __init__(self, spelling: dict, manifest: dict, grid: dict) -> None:
        self.initials = spelling["components"]["initials"]
        self.finals = spelling["components"]["finals"]
        self.medials = spelling["components"]["medials"]
        self.initials_order = spelling["initials_order"]
        self.finals_order = [
            f["key"] for f in manifest["finals"] if f["key"] not in CODA_ONLY
        ]
        self.medial_keys = [m["key"] for m in manifest["medials"]]
        self.implicit_i_initials = set(spelling["implicit_i_initials"])
        self.compound_finals = manifest["compose"]["compound_finals"]
        self.layouts = spelling["layouts"]
        self.grid_romanization = grid.get("romanization", {})

    def _final_glyph(self, key: str) -> dict | None:
        return self.finals.get(key)

    def _initial_glyph(self, key: str) -> dict | None:
        return self.initials.get(key)

    def _medial_glyph(self, key: str) -> dict | None:
        return self.medials.get(key)

    def _precomposed(self, romanization: str) -> dict | None:
        hit = self.grid_romanization.get(romanization)
        if not hit or hit.get("kind") != "syllable":
            return None
        return {
            "codepoint": hit["codepoint"],
            "char": hit["char"],
            "source": "syllable_grid",
        }

    def _compound_parts(self, compound_key: str) -> tuple[str, str] | None:
        parts = self.compound_finals.get(compound_key)
        if not parts or len(parts) != 2:
            return None
        return parts[0], parts[1]

    def simple(self, initial: str, final: str) -> dict | None:
        romanization = initial + final
        parse = {
            "initial": initial,
            "medial": None,
            "final": final,
            "compound": False,
        }
        slots = {
            "top": self._initial_glyph(initial),
            "bottom": self._final_glyph(final),
        }
        return compose_entry(
            romanization=romanization,
            parse=parse,
            layout="simple",
            rule=1,
            slots=slots,
            slot_order=self.layouts["simple"]["slot_order"],
            precomposed=self._precomposed(romanization),
        )

    def implicit_i_syllable(self, initial: str, final: str) -> dict | None:
        if final == "i":
            romanization = initial + "i"
        else:
            romanization = initial + "i" + final
        parse = {
            "initial": initial,
            "medial": None,
            "medial_phonemic": "i",
            "medial_glyph_suppressed": True,
            "final": final,
            "compound": False,
        }
        slots = {
            "top": self._initial_glyph(initial),
            "bottom": self._final_glyph(final),
        }
        return compose_entry(
            romanization=romanization,
            parse=parse,
            layout="simple",
            rule=3,
            slots=slots,
            slot_order=self.layouts["simple"]["slot_order"],
            precomposed=self._precomposed(romanization),
        )

    def with_medial(self, initial: str, medial: str, final: str) -> dict | None:
        romanization = initial + medial + final
        parse = {
            "initial": initial,
            "medial": medial,
            "final": final,
            "compound": False,
        }
        slots = {
            "top": self._initial_glyph(initial),
            "bottom_left": self._medial_glyph(medial),
            "right": self._final_glyph(final),
        }
        return compose_entry(
            romanization=romanization,
            parse=parse,
            layout="with_medial",
            rule=2,
            slots=slots,
            slot_order=self.layouts["with_medial"]["slot_order"],
        )

    def compound_simple(self, initial: str, compound_key: str) -> dict | None:
        parts = self._compound_parts(compound_key)
        if not parts:
            return None
        p1, p2 = parts
        romanization = initial + compound_key
        parse = {
            "initial": initial,
            "medial": None,
            "final": compound_key,
            "compound": True,
            "final_parts": [p1, p2],
        }
        slots = {
            "top": self._initial_glyph(initial),
            "bottom": self._final_glyph(p1),
            "right": self._final_glyph(p2),
        }
        return compose_entry(
            romanization=romanization,
            parse=parse,
            layout="initial_with_compound_final",
            rule=4,
            slots=slots,
            slot_order=self.layouts["initial_with_compound_final"]["slot_order"],
        )

    def compound_with_medial(
        self, initial: str, medial: str, compound_key: str
    ) -> dict | None:
        parts = self._compound_parts(compound_key)
        if not parts:
            return None
        p1, p2 = parts
        romanization = initial + medial + compound_key
        parse = {
            "initial": initial,
            "medial": medial,
            "final": compound_key,
            "compound": True,
            "final_parts": [p1, p2],
        }
        slots = {
            "top": self._initial_glyph(initial),
            "bottom_left": self._medial_glyph(medial),
            "right_bottom": self._final_glyph(p1),
            "right_top": self._final_glyph(p2),
        }
        return compose_entry(
            romanization=romanization,
            parse=parse,
            layout="with_medial_and_compound_final",
            rule=4,
            slots=slots,
            slot_order=self.layouts["with_medial_and_compound_final"]["slot_order"],
        )


def build() -> dict:
    spelling = load_json(SPELLING_PATH)
    manifest = load_json(MANIFEST_PATH)
    grid = load_json(GRID_PATH)
    composer = Composer(spelling, manifest, grid)

    entries: dict[str, dict] = {}
    stats = {
        "simple": 0,
        "implicit_i": 0,
        "with_medial": 0,
        "compound_simple": 0,
        "compound_with_medial": 0,
        "skipped_incomplete": 0,
        "alternate_decompositions": 0,
    }

    def add(entry: dict | None, bucket: str) -> None:
        if entry is None:
            stats["skipped_incomplete"] += 1
            return
        key = entry["romanization"]
        if key in entries:
            existing = entries[key]
            alt = {
                "parse": entry["parse"],
                "layout": entry["layout"],
                "rule": entry["rule"],
                "glyphs": entry["glyphs"],
                "glyph_string": entry["glyph_string"],
                "codepoints": entry["codepoints"],
            }
            existing.setdefault("alternates", []).append(alt)
            stats["alternate_decompositions"] += 1
            return
        entries[key] = entry
        stats[bucket] += 1

    initials = composer.initials_order
    finals = composer.finals_order
    medials = composer.medial_keys
    compounds = list(composer.compound_finals.keys())
    implicit = [i for i in initials if i in composer.implicit_i_initials]

    # Rule 1: initial + final (grid syllables)
    for ini in initials:
        for fin in finals:
            add(composer.simple(ini, fin), "simple")

    # Rule 3: implicit-i spellings (e.g. shian)
    for ini in implicit:
        for fin in finals:
            if fin == "i":
                continue  # covered by simple ini+"i"
            add(composer.implicit_i_syllable(ini, fin), "implicit_i")

    # Rule 2: initial + medial + final
    for ini in initials:
        for med in medials:
            if ini in composer.implicit_i_initials and med == "i":
                continue
            for fin in finals:
                add(composer.with_medial(ini, med, fin), "with_medial")

    # Rule 4: compound finals without medial
    for ini in initials:
        for compound in compounds:
            add(composer.compound_simple(ini, compound), "compound_simple")

    # Rule 4 + 2: compound finals with medial
    for ini in initials:
        for med in medials:
            if ini in composer.implicit_i_initials and med == "i":
                continue
            for compound in compounds:
                add(composer.compound_with_medial(ini, med, compound), "compound_with_medial")

    precomposed_count = sum(1 for e in entries.values() if "precomposed" in e)

    return {
        "meta": {
            "description": (
                "Complete Goetsusioji spelling → component glyph mapping. "
                "Each entry lists the glyph sequence per 拼寫規則 layout slots."
            ),
            "generated_by": "scripts/build_complete_mapping.py",
            "sources": [
                "data/spelling-compose-rules.json",
                "data/chart-manifest.json",
                "data/glyphs-handfill-with-chinese.json",
                "mapping/goetsuese-mapping.json",
            ],
            "total_entries": len(entries),
            "stats": stats,
            "precomposed_grid_matches": precomposed_count,
            "initial_count": len(initials),
            "syllable_final_count": len(finals),
            "medial_count": len(medials),
            "compound_final_count": len(compounds),
            "collision_policy": (
                "Romanization string is the lookup key. When the same string arises from "
                "more than one decomposition (e.g. tiu = t+iu simple vs t+i+u medial), "
                "the first tier wins (simple > implicit_i > with_medial > compound). "
                "Other decompositions are listed under alternates."
            ),
            "layouts_used": [
                "simple",
                "with_medial",
                "initial_with_compound_final",
                "with_medial_and_compound_final",
            ],
        },
        "entries": dict(sorted(entries.items())),
    }


def main() -> int:
    out = build()
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    meta = out["meta"]
    print(f"Wrote {OUT_PATH}")
    print(f"  total entries: {meta['total_entries']}")
    print(f"  stats: {meta['stats']}")
    print(f"  precomposed grid matches: {meta['precomposed_grid_matches']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
