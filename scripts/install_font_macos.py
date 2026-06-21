#!/usr/bin/env python3
"""Install goetsusioji.ttf to ~/Library/Fonts with family name Goetsusioji."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "goetsusioji.ttf"
DST = Path.home() / "Library" / "Fonts" / "Goetsusioji.ttf"
FAMILY = "Goetsusioji"


def patch_names(font: TTFont) -> None:
    name = font["name"]
    for rec in name.names:
        if rec.nameID in (1, 3, 4, 6, 16, 17):
            platform = rec.platformID, rec.platEncID, rec.langID
            if rec.nameID == 1:
                name.setName(FAMILY, *platform)
            elif rec.nameID == 4:
                name.setName(FAMILY, *platform)
            elif rec.nameID == 6:
                name.setName("Goetsusioji-Regular", *platform)
            elif rec.nameID == 3:
                name.setName(f"{FAMILY}:Version 1.00", *platform)


def main() -> int:
    if not SRC.exists():
        print(f"Missing font: {SRC}", file=sys.stderr)
        return 1

    DST.parent.mkdir(parents=True, exist_ok=True)
    font = TTFont(SRC)
    patch_names(font)
    font.save(DST)
    font.close()
    print(f"Installed {DST}")
    print("Reload Cursor/VS Code window for the font to take effect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
