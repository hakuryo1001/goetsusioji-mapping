"""Lookup helpers for Goetsuese PUA mappings."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_MAPPING = Path(__file__).resolve().parents[1] / "mapping" / "goetsuese-mapping.json"


class GoetsueseMapper:
    def __init__(self, mapping_path: Path | str | None = None) -> None:
        path = Path(mapping_path) if mapping_path else DEFAULT_MAPPING
        with path.open(encoding="utf-8") as f:
            self.data = json.load(f)
        self.initials = self.data["initials_order"]
        self.finals = self.data["finals_order"]
        self.syllables = self.data["syllables"]
        self.romanization = self.data["romanization"]
        self.grammar = self.data.get("grammar", {})

    def split_syllable(self, text: str) -> tuple[str, str] | None:
        text = text.strip().lower()
        if not text:
            return None
        for ini in sorted(self.initials, key=len, reverse=True):
            if not text.startswith(ini):
                continue
            rest = text[len(ini) :]
            for fin in sorted(self.finals, key=len, reverse=True):
                if rest == fin:
                    return ini, fin
        return None

    def syllable(self, initial: str, final: str) -> dict | None:
        return self.syllables.get(f"{initial}+{final}")

    def from_romanization(self, text: str) -> dict | None:
        return self.romanization.get(text.strip().lower())

    def grammar_marker(self, key: str) -> dict | None:
        return self.grammar.get(key)

    def transliterate_words(self, phrase: str) -> list[dict]:
        """Map space-separated romanization tokens to glyphs where possible."""
        out: list[dict] = []
        for token in phrase.strip().split():
            token = token.strip("[]")
            if token in self.grammar:
                out.append({"token": token, "type": "grammar", **self.grammar[token]})
                continue
            parsed = self.split_syllable(token)
            if parsed:
                ini, fin = parsed
                mapping = self.syllable(ini, fin)
                out.append(
                    {
                        "token": token,
                        "type": "syllable",
                        "parse": {"initial": ini, "final": fin},
                        "mapping": mapping,
                    }
                )
            else:
                direct = self.from_romanization(token)
                out.append(
                    {
                        "token": token,
                        "type": "syllable" if direct else "unknown",
                        "mapping": direct,
                    }
                )
        return out

    def transliterate_text(self, phrase: str) -> str:
        chars: list[str] = []
        for item in self.transliterate_words(phrase):
            mapping = item.get("mapping")
            if isinstance(mapping, dict) and "char" in mapping:
                chars.append(mapping["char"])
            elif item.get("char"):
                chars.append(item["char"])
            else:
                chars.append(f"[{item['token']}]")
        return "".join(chars)
