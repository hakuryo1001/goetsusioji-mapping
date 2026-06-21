#!/usr/bin/env python3
"""Render PUA glyphs from goetsusioji.ttf for visual verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT.parent / "goetsusioji-reference" / "goetsusioji.ttf"
MAPPING = ROOT / "mapping" / "goetsuese-mapping.json"


def render_char(ch: str, size: int = 128, px: int = 160) -> Image.Image:
    font = ImageFont.truetype(str(FONT), px)
    img = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), ch, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1]
    draw.text((x, y), ch, font=font, fill=0)
    return img


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "output" / "glyphs")
    parser.add_argument("--components-only", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    with MAPPING.open(encoding="utf-8") as f:
        data = json.load(f)

    items: list[tuple[str, str]] = []
    for key, entry in data["initials"].items():
        items.append((f"initial_{key}", entry["char"]))
    if not args.components_only:
        for key, entry in data["syllables"].items():
            items.append((f"syl_{key.replace('+', '_')}", entry["char"]))
        for key, entry in data.get("grammar", {}).items():
            items.append((f"grammar_{key}", entry["char"]))

    for name, ch in items:
        render_char(ch).save(args.out / f"{name}.png")

    print(f"Rendered {len(items)} glyphs to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
