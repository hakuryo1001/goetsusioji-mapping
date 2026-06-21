#!/usr/bin/env python3
"""CLI for Goetsuese romanization lookup."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from goetsuese_typer import GoetsueseMapper


def main() -> int:
    parser = argparse.ArgumentParser(description="Goetsuese romanization → PUA lookup")
    parser.add_argument("text", nargs="?", help="Romanization text (space-separated syllables)")
    parser.add_argument("--json", action="store_true", help="Print structured JSON")
    parser.add_argument("--syllable", help="Look up one syllable, e.g. le or t+aon")
    parser.add_argument("--grammar", help="Look up grammar marker, e.g. tsy")
    args = parser.parse_args()

    mapper = GoetsueseMapper()

    if args.syllable:
        if "+" in args.syllable:
            ini, fin = args.syllable.split("+", 1)
            result = mapper.syllable(ini, fin)
        else:
            result = mapper.from_romanization(args.syllable) or (
                mapper.split_syllable(args.syllable)
                and mapper.syllable(*mapper.split_syllable(args.syllable))  # type: ignore
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.grammar:
        print(json.dumps(mapper.grammar_marker(args.grammar), ensure_ascii=False, indent=2))
        return 0

    if not args.text:
        parser.print_help()
        return 1

    if args.json:
        print(json.dumps(mapper.transliterate_words(args.text), ensure_ascii=False, indent=2))
    else:
        print(mapper.transliterate_text(args.text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
