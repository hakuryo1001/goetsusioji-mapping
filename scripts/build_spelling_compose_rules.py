#!/usr/bin/env python3
"""Build spelling-compose-rules.json from glyphs-handfill-with-chinese.json + chart-manifest."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLYPHS_PATH = ROOT / "data" / "glyphs-handfill-with-chinese.json"
MANIFEST_PATH = ROOT / "data" / "chart-manifest.json"
OUT_PATH = ROOT / "data" / "spelling-compose-rules.json"

ALIASES = {
    "ch(i)": "ch",
    "c(i)": "c",
    "j(i)": "j",
    "sh(i)": "sh",
    "zh(i)": "zh",
    "ae(n)": "ae",
    "oe(n)": "oe",
    "ie(n)": "ie",
    "zero | null": "zero",
    "mh | m": "mh",
    "hn": "-n",
    "hq": "-q",
}


def norm_rom(raw: str) -> list[str]:
    if not raw or not raw.strip():
        return []
    return [ALIASES.get(p.strip().lower(), p.strip().lower()) for p in raw.split("|")]


def glyph_entry(cp_key: str, entry: dict) -> dict:
    out = {
        "codepoint": cp_key,
        "char": entry.get("char", ""),
        "romanization": entry.get("romanization", ""),
    }
    if entry.get("chinese character only orthography"):
        out["hanzi_hint"] = entry["chinese character only orthography"]
    if entry.get("role"):
        out["role"] = entry["role"]
    if entry.get("notes"):
        out["notes"] = entry["notes"]
    return out


def build() -> dict:
    with GLYPHS_PATH.open(encoding="utf-8") as f:
        glyphs_data = json.load(f)
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        manifest = json.load(f)

    glyphs = glyphs_data["glyphs"]
    initials: dict[str, dict] = {}
    finals: dict[str, dict] = {}
    medials: dict[str, dict] = {}
    dual_role: dict[str, dict] = {}

    for cp_key, entry in glyphs.items():
        rom = entry.get("romanization", "")
        role = entry.get("role", "")
        keys = norm_rom(rom)
        if not keys:
            continue
        g = glyph_entry(cp_key, entry)
        if "initial" in role:
            for k in keys:
                initials[k] = g
        if "final" in role:
            for k in keys:
                finals[k] = g
        if "medial" in role:
            for k in keys:
                medials[k] = g
        if "final | medial" in role:
            for k in keys:
                dual_role[k] = g

    for cp_key, entry in glyphs.items():
        rom = entry.get("romanization", "")
        if rom == "hn":
            finals["-n"] = glyph_entry(cp_key, entry)
        elif rom == "hq":
            finals["-q"] = glyph_entry(cp_key, entry)

    for k in [m["key"] for m in manifest.get("medials", [])]:
        if k not in medials and k in dual_role:
            medials[k] = dual_role[k]
        elif k not in medials and k in finals:
            medials[k] = {**finals[k], "shared_with_final": True}

    initial_order = [x["key"] for x in manifest["initials"]]
    final_order = [x["key"] for x in manifest["finals"]]
    implicit_i = manifest["compose"]["implicit_i_initials"]
    compound_finals = manifest["compose"]["compound_finals"]

    compound_glyphs = {}
    for cf_key, parts in compound_finals.items():
        bottom_key, right_key = parts
        compound_glyphs[cf_key] = {
            "parts": parts,
            "layout": "bottom_right",
            "bottom": finals.get(bottom_key),
            "right": finals.get(right_key),
            "complete": bottom_key in finals and right_key in finals,
        }

    examples = [
        {
            "romanization": "keq",
            "hanzi": "個",
            "rule": 1,
            "parse": {"initial": "k", "final": "eq"},
            "layout": "simple",
            "slots": {"top": initials.get("k"), "bottom": finals.get("eq")},
        },
        {
            "romanization": "tiau",
            "hanzi": "鳥",
            "rule": 2,
            "parse": {"initial": "t", "medial": "i", "final": "au"},
            "layout": "with_medial",
            "slots": {
                "top": initials.get("t"),
                "bottom_left": medials.get("i"),
                "right": finals.get("au"),
            },
        },
        {
            "romanization": "shian",
            "hanzi": "向",
            "rule": 3,
            "parse": {
                "initial": "sh",
                "medial": None,
                "medial_phonemic": "i",
                "final": "an",
            },
            "layout": "simple",
            "note": "sh contains implicit i; do not render i medial glyph",
            "slots": {"top": initials.get("sh"), "bottom": finals.get("an")},
        },
        {
            "romanization": "maeq",
            "hanzi": "襪",
            "rule": 4,
            "parse": {
                "initial": "m",
                "final": "aeq",
                "final_decomposition": compound_finals["aeq"],
            },
            "layout": "initial_with_compound_final",
            "slots": {
                "top": initials.get("m"),
                "bottom": finals.get("ae"),
                "right": finals.get("-q"),
            },
        },
        {
            "romanization": "yu",
            "hanzi": None,
            "rule": 5,
            "parse": {
                "note": "Optional explicit yu marking when 尖團 distinction is needed",
                "components_phonemic": ["y", "i"],
            },
            "layout": "simple",
            "chart_notation": "厶𠄎",
            "handfill_notation": "云+兀",
            "slots": {"top": finals.get("y"), "bottom": medials.get("i")},
        },
    ]

    for ex in examples:
        missing = [slot for slot, g in ex.get("slots", {}).items() if g is None]
        ex["ready"] = not missing
        if missing:
            ex["missing_slots"] = missing

    rules_zh = [
        {
            "id": 1,
            "title_zh": "一般字音",
            "title_en": "Simple syllable (initial + final)",
            "text_zh": "聲母符號和韻母符號拼合起來就可以表達一個字音，拼寫時聲母在上，韻母在下。",
            "example_zh": "個(keq)：聲母 k「工」+ 韻母 eq「出」",
            "layout": "simple",
        },
        {
            "id": 2,
            "title_zh": "含有介音的字音",
            "title_en": "Syllable with medial",
            "text_zh": "拼寫時聲母在上，介母在其下，韻母在介母之右。",
            "example_zh": "鳥(tiau)：聲母 t + 介母 i + 韻母 au",
            "layout": "with_medial",
        },
        {
            "id": 3,
            "title_zh": "聲母斤組與興組",
            "title_en": "Implicit-i initials (斤 / 兴 groups)",
            "text_zh": "ch(i)、c(i)、j(i) 和 sh(i)、zh(i) 視為已含介母 i，因此不用再標出介音 i。",
            "example_zh": "向(shian)：sh + an（省略介母 i 符號）",
            "layout": "simple",
            "implicit_i_initials": implicit_i,
        },
        {
            "id": 4,
            "title_zh": "表述各地方言時",
            "title_en": "Dialectal / decomposed finals",
            "text_zh": "aeq、oeq、eoq、ai、ei 等有專門寫法（下+右布局），同時按照介音字的方式進行拼寫。",
            "example_zh": "襪(maeq)：m + aeq（万 + く）",
            "layout": "compound_final",
            "compound_finals": list(compound_finals.keys()),
            "chart_hanzi_notation": {
                "aeq": "万く",
                "oeq": "寒く",
                "eoq": "能く",
                "ai": "兀万",
                "ei": "工万",
            },
        },
        {
            "id": 5,
            "title_zh": "撮口音 iu",
            "title_en": "Rounded medial iu (no yu distinction)",
            "text_zh": "由於目前撮口音 iu 基本上不區分尖團，所以不再單獨設立 yu 韻母；如需表記，記音為「厶𠄎」（handfill: 云+兀）。",
            "layout": "simple",
            "note": "Normal iu-medial syllables use medial iu (U+F531) + final; this rule is only for explicit yu marking.",
        },
    ]

    return {
        "meta": {
            "source": [
                "goetsusioji-mapping/pics/3.png",
                "data/chart-tables-handfill.md#section-3",
                "data/glyphs-handfill-with-chinese.json",
                "data/chart-manifest.json",
            ],
            "description": "Spelling / composition rules (拼寫規則) for Goetsusioji.",
            "generated_by": "scripts/build_spelling_compose_rules.py",
            "component_glyph_range": "U+F500..U+F545",
            "precomposed_syllable_grid": "U+F040..U+F4F9",
            "programmatic_readiness": {
                "summary": "Mostly yes for parsing and component lookup; not yet for rendering composed glyphs outside the precomposed grid.",
                "ready": [
                    "Component glyph lookup by initial/final/medial key",
                    "Layout selection (simple / with_medial / compound_final)",
                    "Implicit-i suppression for 斤/兴 initials",
                    "Compound final decomposition (aeq, oeq, eoq, ai, ei)",
                    "Precomposed grid lookup for plain initial+final (no medial)",
                ],
                "gaps": [
                    "Medial syllables (tiau, tuan, etc.) are not in the 39×26 precomposed grid",
                    "No fully composed example codepoints filled in chart-tables-handfill.md §3.3",
                    "Font may lack pre-built ligatures for arbitrary component stacks",
                    "Tone marks have no assigned component codepoints yet",
                    "Romanization keys hn/hq in handfill are coda components -n/-q",
                ],
            },
        },
        "rules_zh_full": {"title": "拼寫規則", "rules": rules_zh},
        "layouts": {
            "simple": {
                "description_zh": "声母在上，韵母在下",
                "description_en": "initial above final",
                "slot_order": ["top", "bottom"],
                "slot_roles": {"top": "initial", "bottom": "final"},
            },
            "with_medial": {
                "description_zh": "声母在上，介母在其下，韵母在介母之右",
                "description_en": "initial top-left; medial below initial; final to the right",
                "slot_order": ["top", "bottom_left", "right"],
                "slot_roles": {
                    "top": "initial",
                    "bottom_left": "medial",
                    "right": "final",
                },
            },
            "compound_final": {
                "description_zh": "韵母两部分：下+右",
                "description_en": "final split into bottom + right parts",
                "slot_order": ["bottom", "right"],
                "slot_roles": {"bottom": "final_part_1", "right": "final_part_2"},
            },
            "initial_with_compound_final": {
                "description_zh": "声母在上；韵母用下+右拼合（无介母）",
                "description_en": "initial on top; decomposed final below and right",
                "slot_order": ["top", "bottom", "right"],
                "slot_roles": {
                    "top": "initial",
                    "bottom": "final_part_1",
                    "right": "final_part_2",
                },
            },
            "with_medial_and_compound_final": {
                "description_zh": "声母在上，介母在其下，复合韵母在右侧",
                "description_en": "initial top; medial below; compound final on the right",
                "slot_order": ["top", "bottom_left", "right_bottom", "right_top"],
                "slot_roles": {
                    "top": "initial",
                    "bottom_left": "medial",
                    "right_bottom": "final_part_1",
                    "right_top": "final_part_2",
                },
                "note": "Inferred from rules 2+4; verify when §3.3 examples are filled.",
            },
        },
        "components": {
            "initials": initials,
            "finals": finals,
            "medials": medials,
            "dual_final_medial": dual_role,
            "romanization_aliases": ALIASES,
            "coda_keys": {
                "-q": "hq in handfill (U+F53B, く coda)",
                "-n": "hn in handfill (U+F53A, レ coda)",
            },
        },
        "initials_order": initial_order,
        "finals_order": final_order,
        "implicit_i_initials": implicit_i,
        "compound_finals": compound_glyphs,
        "medials_meta": manifest.get("medials", []),
        "tones": manifest.get("tones", []),
        "compose_algorithm": {
            "description": "Suggested parse → layout → glyph slots pipeline",
            "steps": [
                "Normalize romanization (lowercase; expand ae(n)→ae etc.)",
                "If entire string matches precomposed grid (initial+final, no medial), use grid glyph",
                "Match longest initial from initials_order",
                "If remainder starts with medial key (iu before i) AND initial not in implicit_i_initials, consume medial",
                "If initial in implicit_i_initials and remainder starts with i, treat i as part of palatalized onset",
                "Match remainder as final: compound_finals keys first, else finals_order longest-first",
                "Select layout from parse shape",
                "Map each slot to component codepoint",
            ],
            "medial_detection_order": ["iu", "i", "u", "r"],
            "prefer_precomposed_grid_when": "no explicit medial AND final is not compound AND grid cell exists",
        },
        "examples": examples,
    }


def main() -> int:
    out = build()
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    meta = out["meta"]["programmatic_readiness"]
    print(f"Wrote {OUT_PATH}")
    print(f"  components: {len(out['components']['initials'])} initials, {len(out['components']['finals'])} finals")
    print(f"  examples ready: {sum(1 for e in out['examples'] if e['ready'])}/{len(out['examples'])}")
    print(f"  readiness: {meta['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
