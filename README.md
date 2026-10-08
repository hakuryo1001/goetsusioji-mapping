# Goetsusioji Mapping

Romanization → **Siauzy** (Goetsu Xiaozi PUA glyphs) and **Han progenitor spelling** for Wu Xiaozi (吳小字 / Goetsuese).

## Two files

| File | Role |
| --- | --- |
| [`handfilling/glyphs-handfill-with-chinese.json`](handfilling/glyphs-handfill-with-chinese.json) | **Hand-edited source.** Per-codepoint glyph inventory + `chart` section (initials, finals, medials, codas, compound finals, tones, spelling decisions). |
| [`mapping/goetsusioji.json`](mapping/goetsusioji.json) | **Generated canonical table.** Every syllable: romanization → Siauzy glyph blocks + Han spelling. This is what the typer should read. |

Do not hand-edit `mapping/goetsusioji.json`. Change the handfill (or `chart` inside it), then rebuild.

## Two outputs per syllable

- **Siauzy** — always canonical font glyphs, laid out as in charts 1–3. Head block is a grid glyph (`U+F040`–`U+F4F9`); beside blocks are header-row finals/codas (`U+F021`–`U+F03B`) only where the rules put a part beside the head. Never CSS-stacked loose components.
- **Han** — progenitor-hanzi string (man'yōgana-style teaching layer), e.g. `keq` → 工出, `tiau` → 刀以号. Independent of the font; available even when a Siauzy head block is missing.

## Build

```bash
python3 scripts/build.py              # write mapping/goetsusioji.json
python3 scripts/build.py lookup tiau shian maeq
python3 scripts/export_chart_reference_md.py   # optional: refresh docs/
```

Dependencies: Python 3.10+, `fonttools` (font checks).

```bash
pip install fonttools
```

## Editor font

PUA glyphs need **Goetsusioji**. See [`.vscode/font-setup.md`](.vscode/font-setup.md).

```bash
python3 scripts/install_font_macos.py   # optional
```

## Charts

Reference images: [`pics/1.png`](pics/1.png) · [`pics/2.png`](pics/2.png) · [`pics/3.png`](pics/3.png)

Human-readable replica: [`docs/goetsu-xiaozi-charts.md`](docs/goetsu-xiaozi-charts.md)

Chart-faithfulness decisions (fricative ゜, final `y`, `aoq`, `shian`, beside-block glyphs, etc.) live under `handfill.chart.decisions`.

## Scripts kept

- `scripts/build.py` — build + validate + `lookup`
- `scripts/export_chart_reference_md.py` — chart markdown
- `scripts/install_font_macos.py` — local font install
