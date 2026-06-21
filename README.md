# Goetsuese Typer

Romanization → PUA glyph mapping for **Wu Xiaozi** (Goetsuese / 吴小字), built from:

- `goetsusioji-reference/goetsusioji.ttf` — font grid (`U+F021`–`U+F545`)
- `goetsusioji-reference/pics/1.png` — initials (聲母表)
- `goetsusioji-reference/pics/2.png` — finals (韻母表)
- `goetsusioji-reference/pics/3.png` — medials, tones, composition rules

## How the encoding works

The font stores glyphs on a **26-column syllable grid**:

- **Columns** = finals (`a`, `o`, `e`, …, `aon`, `r`, `-q`, `-n`) — 26 slots
- **Rows** (from `U+F040` upward) = initials (`ph`, `p`, `b`, …, `w`) — 39 rows
- **Component row** (`U+F021`–`U+F03D`) = standalone initial glyphs (first 29 initials from the chart)

A syllable like `taon` is parsed as initial `t` + final `aon`, then looked up at grid row `t`, column `aon`.

Composition rules (initial above final; medial left; compound finals) describe how glyphs are **drawn**, but in this font each syllable cell is a **single precomposed PUA character**.

## Editor font (this project only)

PUA glyphs in the editor use **Goetsusioji**, not global Jyutcitzi. See [`.vscode/font-setup.md`](.vscode/font-setup.md).

```bash
python3 scripts/install_font_macos.py   # optional: install as "Goetsusioji"
# Then reload the Cursor window
```

Open **`goetsuese-typer`** as the workspace folder so `.vscode/settings.json` applies.

## Quick start

```bash
# Regenerate mapping JSON from font + chart manifest
python3 scripts/build_mapping.py

# Look up syllables
python3 scripts/lookup.py "taon nyie"
python3 scripts/lookup.py --json "le nyie"
python3 scripts/lookup.py --grammar tsy

# Render glyph PNGs for verification
python3 scripts/render_glyphs.py --components-only
```

## Python API

```python
from goetsuese_typer import GoetsueseMapper

m = GoetsueseMapper()
m.from_romanization("taon")   # t + aon → U+F156
m.transliterate_text("taon nyie")
m.grammar_marker("tsy")       # adverbial suffix → U+F3CA
```

## Output files

| File | Contents |
|------|----------|
| `mapping/goetsuese-mapping.json` | Full mapping + metadata |
| `mapping/syllables.json` | `{initial}+{final}` → codepoint |
| `mapping/romanization.json` | compact syllable string → codepoint |
| `mapping/components.json` | initial components, medials, tones, grammar |

## Coverage

- **1,014** syllable cells (39 initials × 26 finals)
- **29** standalone initial component glyphs
- **Grammar**: `tsy` → `U+F3CA` (from reference RTF / ngven.org)
- **Overflow** rows (`U+F500`+) — extra glyphs not on the main syllable grid (see full JSON)

## Caveats

- Romanization parsing uses longest-match on initials/finals; ambiguous strings may need explicit `initial+final` form.
- Some chart finals share the same shape (`a`/`o`/`u`) but map to **different columns** in the grid.
- Medials and tone marks from chart 3 are documented in `data/chart-manifest.json` but are **not yet** assigned separate codepoints in the mapping (may live in overflow rows).
- Validate against your target dialect — this follows the ngven chart ordering.

## Dependencies

- Python 3.10+
- `fonttools` (build script)
- `Pillow` (optional, for `render_glyphs.py`)

```bash
pip install fonttools pillow
```
