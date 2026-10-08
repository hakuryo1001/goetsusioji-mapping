# Derived Chinese Orthography

Generated output from [`scripts/fill_chinese_orthography.py`](../scripts/fill_chinese_orthography.py).

- Source of truth for hand curation remains [`../handfilling/`](../handfilling/).
- Human-readable chart replica: [`../docs/goetsu-xiaozi-charts.md`](../docs/goetsu-xiaozi-charts.md) (pics 1–3).
- Do **not** hand-edit files here; re-run the script instead.
- `glyphs-with-chinese.json` — handfill copy with empty Chinese hints filled by rule
- `validation-report.md` — mismatches against already-handfilled entries plus fill counts

## Chart vs handfill conventions

| Topic | Chart (pics) | This filler / handfill Chinese hints |
| --- | --- | --- |
| Final `y` | 私(空韻) on pic 2 | **厶** (keep handfill) |
| Final `oq` | 昱 on pic 2 | **昱** (same) |
| Fricatives `f` / `s` / `sh` | Pic 1 draws ゜ on the Goetsu glyphs | Hints use unmarked **弗** / **式** / **兴** (do not rewrite) |
| `h` | ゜ on glyph | Hint **奧ﾟ** |
| Codas `-n` / `-q` | レ / く | Specials on `U+F03A`/`U+F03B`/`hn`/`hq` |
| Zero initial | 零聲母 / blank under 奥 | **奧** for `-` and `zero \| null` |
