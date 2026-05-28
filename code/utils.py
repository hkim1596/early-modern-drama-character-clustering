"""Shared helpers."""

from __future__ import annotations
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


def load_play_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def normalize_for_match(name: str) -> str:
    """Lowercase, strip diacritics, replace long-s with s, strip punctuation, collapse whitespace.

    Used only for fuzzy matching — the original spelling is preserved everywhere else.
    """
    if not isinstance(name, str):
        return ""
    s = unicodedata.normalize("NFKC", name)
    s = s.replace("ſ", "s").replace("ß", "ss")
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def clean_speech_text(s: str) -> str:
    """Light cleanup of OCR artifacts. Preserves original orthography otherwise."""
    if not isinstance(s, str):
        return ""
    s = s.replace("•", " ")
    s = s.replace(" ", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def parse_roles_field(roles_str: str) -> list[dict[str, str]]:
    """Extract role names + descriptions from the catalogue's `roles` column.

    Convention: role names are written in ALL CAPS (possibly multi-word, e.g.
    "JOHN OF GAUNT"), sometimes prefixed by a title-case modifier (e.g. "King RICHARD II").
    Descriptions follow until the next ALL CAPS name token.
    """
    if not isinstance(roles_str, str):
        return []

    # A role name is a word containing a run of >=3 consecutive uppercase letters
    # (catches "VIRGINIA", "MANSIPULUS", and mixed-case forms like "vIRGINIUS"),
    # optionally followed by adjacent uppercase-bearing words ("JOHN OF GAUNT",
    # "RICHARD II"). We allow leading lowercase chars before the uppercase run so
    # "vIRGINIUS" parses as one name token.
    NAME_TOKEN = r"[A-Za-z]*[A-Z]{3,}[A-Za-z'.\-]*"
    pattern = re.compile(rf"\b({NAME_TOKEN}(?:\s+{NAME_TOKEN})*)\b")
    matches = list(pattern.finditer(roles_str))
    if not matches:
        return []

    entries: list[dict[str, str]] = []
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        bare = name.replace(" ", "")
        # Skip Roman numerals on their own (act/scene markers)
        if re.fullmatch(r"[IVXLCM]+", bare):
            continue
        # Skip obvious stage-direction noise tokens
        if bare in {"ACT", "SCENE", "PAGE"}:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(roles_str)
        description = roles_str[start:end].strip().lstrip(",;").strip()
        # Truncate overly long descriptions
        if len(description) > 400:
            description = description[:400].rsplit(" ", 1)[0] + "…"
        entries.append({"name": name, "description": description})
    return entries
