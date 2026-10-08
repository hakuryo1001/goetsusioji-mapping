# 吳小字（Goetsu Xiaozi）— Chart Reference

Faithful, maximal-detail readable replica of the three reference charts.

| Chart | Source image |
| --- | --- |
| 聲母表 | [`pics/1.png`](../pics/1.png) |
| 韻母表 | [`pics/2.png`](../pics/2.png) |
| 介母 · 聲調 · 拼寫規則 | [`pics/3.png`](../pics/3.png) |

## How to read this document

- **Goetsu glyph** columns use Private Use Area characters from the Goetsusioji font.
  Install/configure the font per [`.vscode/font-setup.md`](../.vscode/font-setup.md).
  Without that font you will see empty boxes or fallback tofu.
- **Chinese origin** is the chart’s example / group Han character (what the red glyph is derived from).
- **Codepoint** is the mapped PUA slot in [`handfilling/glyphs-handfill-with-chinese.json`](../handfilling/glyphs-handfill-with-chinese.json).
  Chart-1 initials/finals prefer `U+F500`… where available; syllable-grid duplicates may also exist.
- This file is a **human-readable chart**. Hand-edited source: `handfilling/`.
  Canonical typer table: [`mapping/goetsusioji.json`](../mapping/goetsusioji.json) (from `python3 scripts/build.py`).
- **Siauzy** is always canonical font glyphs (never CSS-stacked).
  **Han** is the progenitor-hanzi spelling (man'yōgana-style teaching layer).

### Chart vs Han-spelling conventions

| Topic | On these charts | In Han spelling |
| --- | --- | --- |
| Final `y` | **私（空韻）** | **厶** |
| Final `oq` | **昱** | **昱** |
| Fricatives `f` / `s` / `sh` | Pic 1 draws **゜** on the Goetsu glyphs | Unmarked 弗 / 式 / 兴 |
| `h` | **゜** on glyph | 奧ﾟ |

---

# Chart 1 — 聲母表 (Initials)

## Introductory text (left panel)

**吳小字**

吳小字是標音文字，由上下部件拼合而成。其部件包括聲母符號、韻母符號（含介母）和聲調符號。
（通常文句中因連續變調，多只標變調而不標本調。）

聲母符號共有 **16** 個，清一色。在符號右上方加 **半濁符號「゜」** 表示送氣；
加 **濁音符號「〃」**（手寫常作「'」）表示全濁。

另外，**l、m、n、ny、ng** 五個聲母預設為濁（陽／下）；加半濁符號「゜」表示清（陰／上）。

共 **33（+5）** 個聲母符號。

*English:* Goetsu Xiaozi is a phonemic script built from stacked components
(initial + final/medial + optional tone). Sixteen basic voiceless initials;
゜ marks aspiration (or yin sonorants); 〃 marks full voicing.

## Initial groups (right panel)

Each row is an **initial-only** glyph (no final). Layout follows the chart’s group blocks.
Diacritic notes describe what pic 1 shows on the red glyph.

| Group | Romanization | Goetsu glyph | Chinese origin | Codepoint | Notes |
| --- | --- | --- | --- | --- | --- |
| 兵 | `ph` |  | 兵 | `U+F500` | aspirated ゜ |
|  | `p` |  | 兵 | `U+F501` | plain |
|  | `b` |  | 兵 | `U+F502` | voiced 〃 |
| 弗 | `f` |  | 弗 | `U+F503` | chart shows ゜ on glyph |
|  | `v` |  | 弗 | `U+F504` | voiced 〃 |
| 矛 | `mh` |  | 矛 | `U+F540` | yin/clear ゜ on sonorant |
|  | `m` |  | 矛 | `U+F540` | default yang sonorant |
| 刀 | `th` |  | 刀 | `U+F506` | aspirated ゜ |
|  | `t` |  | 刀 | `U+F507` | plain |
|  | `d` |  | 刀 | `U+F508` | voiced 〃 |
| 力 | `lh` |  | 力 | `U+F51F` | yin/clear ゜ |
|  | `l` |  | 力 | `U+F509` | default yang sonorant |
| 斤 | `ch(i)` |  | 斤 | `U+F512` | aspirated ゜; implicit medial i |
|  | `c(i)` |  | 斤 | `U+F513` | plain; implicit medial i |
|  | `j(i)` |  | 斤 | `U+F514` | voiced 〃; implicit medial i |
| 兴 | `sh(i)` |  | 兴 | `U+F515` | chart shows ゜; implicit medial i |
|  | `zh(i)` |  | 兴 | `U+F516` | voiced 〃; implicit medial i |
| 拿 | `nh` |  | 拿 | `U+F541` | yin/clear ゜ |
|  | `n` |  | 拿 | `U+F50A` | default yang sonorant |
| 子 | `tsh` |  | 子 | `U+F517` | aspirated ゜ |
|  | `ts` |  | 子 | `U+F518` | plain |
|  | `dz` |  | 子 | `U+F519` | voiced 〃 |
| 式 | `s` |  | 式 | `U+F51A` | chart shows ゜ on glyph |
|  | `z` |  | 式 | `U+F51B` | voiced 〃 |
| 女 | `nyh` |  | 女 | `U+F543` | yin/clear ゜ |
|  | `ny` |  | 女 | `U+F51C` | default yang sonorant |
| 工 | `kh` |  | 工 | `U+F50B` | aspirated ゜ |
|  | `k` |  | 工 | `U+F50C` | plain |
|  | `g` |  | 工 | `U+F50D` | voiced 〃 |
| 奥 | `h` |  | 奥 | `U+F50E` | chart shows ゜ on glyph |
|  | `…` |  | 奥 | `U+F50F` | blank / null onset cell under 奥 (shares zero glyph) |
|  | `gh` |  | 奥 | `U+F510` | voiced 〃 |
| 午 | `nk` |  | 午 | `U+F542` | yin/clear ゜ |
|  | `ng` |  | 午 | `U+F511` | default yang sonorant |
| 零聲母 | `zero | null` |  | 零聲母 | `U+F50F` | zero initial (chart label …) |
| 云 | `i` |  | 云 | `U+F51D` | onset / medial-related; chart pair with y |
|  | `y` |  | 云 | `U+F544` | onset; chart pair with i |
| 危 | `u` |  | 危 | `U+F51E` | onset u / glide |
|  | `w` |  | 危 | `U+F545` | onset w |

### Chart-1 initial components (PUA `U+F500`…), same order as export

| Codepoint | Romanization | Goetsu glyph | Role |
| --- | --- | --- | --- |
| `U+F500` | `ph` |  | initial |
| `U+F501` | `p` |  | initial |
| `U+F502` | `b` |  | initial |
| `U+F503` | `f` |  | initial |
| `U+F504` | `v` |  | initial |
| `U+F506` | `th` |  | initial |
| `U+F507` | `t` |  | initial |
| `U+F508` | `d` |  | initial |
| `U+F509` | `l` |  | initial |
| `U+F50A` | `n` |  | initial |
| `U+F50B` | `kh` |  | initial |
| `U+F50C` | `k` |  | initial |
| `U+F50D` | `g` |  | initial |
| `U+F50E` | `h` |  | initial |
| `U+F50F` | `zero | null` |  | initial |
| `U+F510` | `gh` |  | initial |
| `U+F511` | `ng` |  | initial |
| `U+F512` | `ch(i)` |  | initial |
| `U+F513` | `c(i)` |  | initial |
| `U+F514` | `j(i)` |  | initial |
| `U+F515` | `sh(i)` |  | initial |
| `U+F516` | `zh(i)` |  | initial |
| `U+F517` | `tsh` |  | initial |
| `U+F518` | `ts` |  | initial |
| `U+F519` | `dz` |  | initial |
| `U+F51A` | `s` |  | initial |
| `U+F51B` | `z` |  | initial |
| `U+F51C` | `ny` |  | initial |
| `U+F51D` | `i` |  | initial |
| `U+F51E` | `u` |  | initial |
| `U+F51F` | `lh` |  | initial |
| `U+F540` | `mh | m` |  | initial |
| `U+F541` | `nh` |  | initial |
| `U+F542` | `nk` |  | initial |
| `U+F543` | `nyh` |  | initial |
| `U+F544` | `y` |  | initial |
| `U+F545` | `w` |  | initial |

---

# Chart 2 — 韻母表 (Finals)

## Introductory text (top panel)

基本韻母符號 **24** 個，韻尾符號 **2** 個：促音韻尾 **く（-q）** 和兒化韻尾 **レ（-n）**，
可以用後加的方式來表述具體語境或習慣說法中的臨時音變以及個別地區的特殊韻母。
例如：**aoq（ㄈく）**、**iuq（ミく）**。

此外還有 **1** 個專用符號 **（ㄞ）**，用來表示外來音中 **l/r** 韻尾。總計 **27** 個韻母符號。

*English:* 24 basic finals + 2 coda attachments (-q checked, -n er/nasal) + 1 loanword r/l final = 27.

## Finals grid

Each cell on the chart: **romanization** (top-left) · **Goetsu glyph** (red) · **example Han** (bottom).

| Romanization | Goetsu glyph | Chinese origin (chart) | Codepoint | Notes |
| --- | --- | --- | --- | --- |
| `a` |  | 派 | `U+F021` | — |
| `o` |  | 瓦 | `U+F023` | — |
| `e` |  | 卑 | `U+F025` | — |
| `i` |  | 以 | `U+F027` | also medial 齊齒呼 |
| `u` |  | 无 | `U+F029` | also medial 合口呼 |
| `au` |  | 号 | `U+F02E` | — |
| `ou` |  | 多 | `U+F02F` | — |
| `eu` |  | 久 | `U+F530` | — |
| `iu` |  | 雨 | `U+F531` | also medial 撮口呼 |
| *(empty)* | — | — | — | — |
| `aq` |  | 乏 | `U+F022` | — |
| `oq` |  | 昱 | `U+F024` | chart origin 昱 |
| `eq` |  | 出 | `U+F026` | — |
| `iq` |  | 亦 | `U+F028` | — |
| `q` |  | 促化/塞韻尾 | `U+F03B` | coda **-q**; glyph く-family |
| `ae(n)` |  | 万 | `U+F52B` | ae / ae(n) |
| `oe(n)` |  | 寒 | `U+F532` | oe / oe(n) |
| `en` |  | 文 | `U+F535` | — |
| `ie(n)` |  | 建 | `U+F52D` | ie / ie(n) |
| `n` |  | 兒化/鼻韻尾 | `U+F03A` | coda **-n**; glyph レ |
| `an` |  | 良 | `U+F533` | — |
| `on` |  | 从 | `U+F534` | — |
| `eon` |  | 能 | `U+F538` | — |
| `in` |  | 刃 | `U+F536` | — |
| `y` |  | 私（空韻） | `U+F02A` | chart 私; handfill Chinese hint often 厶 |
| `aon` |  | 亡 | `U+F537` | — |
| *(empty)* | — | — | — | — |
| *(empty)* | — | — | — | — |
| *(empty)* | — | — | — | — |
| `r` |  | 而 | `U+F539` | loanword l/r; dedicated ㄞ |

### Chart-2 / component finals (`role` contains final)

| Codepoint | Romanization | Goetsu glyph | Role |
| --- | --- | --- | --- |
| `U+F521` | `a` |  | final |
| `U+F522` | `aq` |  | final |
| `U+F523` | `o` |  | final |
| `U+F524` | `oq` |  | final |
| `U+F525` | `e` |  | final |
| `U+F526` | `eq` |  | final |
| `U+F527` | `i` |  | final | medial |
| `U+F528` | `iq` |  | final |
| `U+F529` | `u` |  | final | medial |
| `U+F52A` | `y` |  | final |
| `U+F52B` | `ae(n)` |  | final |
| `U+F52D` | `ie(n)` |  | final |
| `U+F52E` | `au` |  | final |
| `U+F52F` | `ou` |  | final |
| `U+F530` | `eu` |  | final |
| `U+F531` | `iu` |  | final | medial |
| `U+F532` | `oe(n)` |  | final |
| `U+F533` | `an` |  | final |
| `U+F534` | `on` |  | final |
| `U+F535` | `en` |  | final |
| `U+F536` | `in` |  | final |
| `U+F537` | `aon` |  | final |
| `U+F538` | `eon` |  | final |
| `U+F539` | `r` |  | final | medial |
| `U+F53A` | `hn` |  | final |
| `U+F53B` | `hq` |  | final |

---

# Chart 3 — 介母 · 聲調 · 拼寫規則

## 介母表 (Medials)

介母符號 **3** 個；另外 1 個翹舌介母 **而（r）**，供部分地區殘留翹舌與外來詞使用。

| Romanization | Goetsu glyph | Chinese label (chart) | Codepoint | Notes |
| --- | --- | --- | --- | --- |
| `i` |  | 以（齊齒呼） | `U+F527` | final | medial |
| `u` |  | 无（合口呼） | `U+F529` | final | medial |
| `iu` |  | 雨（撮口呼） | `U+F531` | final | medial |
| `r` |  | 而（翹舌） | `U+F539` | final | medial |

## 聲調表 (Tones)

聲調符號 **4** 個；變調符號 **3** 個。聲調分陰陽，**由聲母的清濁決定**。
因連續變調，句中單字本調通常不必標出。

| Category | Mark (romanization) | Chart symbol | Notes |
| --- | --- | --- | --- |
| 平 (level) | `-` (often unmarked) | horizontal dash | Yin/Yang by initial voicing |
| 上 (rising) | `'` / ´ | rising stroke | |
| 去 (departing) | `` ` `` / `ˋ` | falling stroke | |
| 入 (entering) | `-q` | `<` | expressed via checked final |
| 變調 | `-x` | dash | sandhi |
| 變調 | `-·` | middle dot `·` | sandhi |

## 拼寫規則 (Spelling rules)

### 1. 一般字音 — initial above final

聲母在上，韻母在下。

| Syllable | Chart Han | Siauzy | Codepoint(s) | Han spelling | Decomposition |
| --- | --- | --- | --- | --- | --- |
| `keq` | 個 |  | `U+F226` | 工出 | k + eq |

Component glyphs: `k`= (`U+F50C`); `eq`= (`U+F526`)

### 2. 含介母字音 — initial + medial + final

聲母在上；介母在聲母之下；韻母在介母之右。

| Syllable | Chart Han | Siauzy | Codepoint(s) | Han spelling | Decomposition |
| --- | --- | --- | --- | --- | --- |
| `tiau` | 鳥 |  | `U+F147`, `U+F02E` | 刀以号 | ti head + au beside |

Component glyphs: `t`= (`U+F507`); `i`= (`U+F51D`); `au`= (`U+F52E`)

### 3. 隱含介母 i — ch(i)/c(i)/j(i)、sh(i)/zh(i)

斤組、兴組聲母視為已含介母 i，不再另寫介母「以」。

| Syllable | Chart Han | Siauzy | Codepoint(s) | Han spelling | Decomposition |
| --- | --- | --- | --- | --- | --- |
| `shian` | 向 |  | `U+F373` | 兴良 | shan head block (alias shan→shian) |

Component glyphs: `sh(i)`= (`U+F515`); `an`= (`U+F533`)

### 4. 方言韻母 — aeq / oeq / eoq / ai / ei

地方韻母可用「下 + 右」拼合（與介母布局類似）。
Chart notes forms such as aeq、oeq、eoq 與 ai、ei。

| Syllable | Chart Han | Siauzy | Codepoint(s) | Han spelling | Notes |
| --- | --- | --- | --- | --- | --- |
| `maeq` | 襪 |  | `U+F0EB`, `U+F03B` | 矛万く | mae head + -q beside |
| `aeq` | — |  | `U+F28B`, `U+F03B` | 奧万く | ae + -q |
| `oeq` | — |  | `U+F292`, `U+F03B` | 奧寒く | oe + -q |
| `eoq` | — |  | `U+F298`, `U+F03B` | 奧能く | eon + -q |
| `ai` | — |  | `U+F281`, `U+F027` | 奧派以 | a + i |
| `ei` | — |  | `U+F285`, `U+F027` | 奧卑以 | e + i |

### 5. 撮口介母 iu

撮口介母 iu 一般不另立 yu 韻；尖團多已合流。需要時用 grid `yu`（y+u）。

| Syllable | Chart Han | Siauzy | Codepoint(s) | Han spelling | Notes |
| --- | --- | --- | --- | --- | --- |
| `yu` | — |  | `U+F4A9` | 云无 | y-initial + u-final grid block |

Medial `iu` glyph: `iu`= (`U+F531`)

---

## Maintenance

Regenerate the canonical mapping, then this file:

```bash
python3 scripts/build.py
python3 scripts/export_chart_reference_md.py
```

Glyphs come from `handfilling/glyphs-handfill-with-chinese.json`;
rule examples pull Siauzy/Han from `mapping/goetsusioji.json`.
