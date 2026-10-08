# Chinese orthography validation report

- Input: `handfilling/glyphs-handfill-with-chinese.json`
- Output: `derived/glyphs-with-chinese.json`
- Newly filled empty fields: **333**
- Already filled and matching rules: **668**
- Mismatches (handfill ≠ rule): **35**
- Entries with romanization but no rule / still empty: **0**
- Entries with empty romanization (skipped): **47**

## Mismatches

| codepoint | romanization | handfill | expected |
| --- | --- | --- | --- |
| U+F079 | `phr` | 兵而 | 兵ﾟ而 |
| U+F132 | `thae` | 刀ﾟ寒 | 刀ﾟ万 |
| U+F133 | `thoe` | 刀ﾟ良 | 刀ﾟ寒 |
| U+F1B1 | `lhi` | 力ﾟ雨 | 力ﾟ以 |
| U+F1CA | `ny` | 拿厶 | 女 |
| U+F1D9 | `nhr` | 拿而 | 拿ﾟ而 |
| U+F2D8 | `gheon` | 午能 | 奧ﾞ能 |
| U+F2D9 | `ghr` | 午而 | 奧ﾞ而 |
| U+F2E6 | `ngeq` | 午ﾟ出 | 午出 |
| U+F2E7 | `ngi` | 午ﾟ以 | 午以 |
| U+F2E8 | `ngiq` | 午ﾟ亦 | 午亦 |
| U+F2E9 | `ngu` | 午ﾟ无 | 午无 |
| U+F2EA | `ngy` | 午ﾟ厶 | 午厶 |
| U+F2EB | `ngae` | 午ﾟ万 | 午万 |
| U+F2ED | `ngie` | 午ﾟ建 | 午建 |
| U+F2EE | `ngau` | 午ﾟ号 | 午号 |
| U+F2EF | `ngou` | 午ﾟ多 | 午多 |
| U+F2F0 | `ngeu` | 午ﾟ久 | 午久 |
| U+F2F1 | `ngiu` | 午ﾟ雨 | 午雨 |
| U+F2F2 | `ngoe` | 午ﾟ寒 | 午寒 |
| U+F2F3 | `ngan` | 午ﾟ良 | 午良 |
| U+F2F4 | `ngon` | 午ﾟ从 | 午从 |
| U+F2F5 | `ngen` | 午ﾟ文 | 午文 |
| U+F2F6 | `ngin` | 午ﾟ刃 | 午刃 |
| U+F2F7 | `ngaon` | 午ﾟ亡 | 午亡 |
| U+F2F8 | `gheon` | 午ﾟ能 | 奧ﾞ能 |
| U+F2F9 | `ghr` | 午ﾟ而 | 奧ﾞ而 |
| U+F30E | `chau` | 斤ﾟ久 | 斤ﾟ号 |
| U+F32E | `cau` | 斤久 | 斤号 |
| U+F357 | `jaon` | 斤ﾟ亡 | 斤ﾞ亡 |
| U+F358 | `jeon` | 斤ﾟ能 | 斤ﾞ能 |
| U+F359 | `jr` | 斤ﾟ而 | 斤ﾞ而 |
| U+F397 | `zhaon` | 兴ﾟ亡 | 兴ﾞ亡 |
| U+F398 | `zheon` | 兴ﾟ能 | 兴ﾞ能 |
| U+F399 | `zhr` | 兴ﾟ而 | 兴ﾞ而 |

## Unfilled (no rule)

_None._
