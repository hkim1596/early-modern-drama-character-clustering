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


def derive_display_columns(df):
    """Add the flat display columns stages 06/07 expect (author, genre,
    company, play_type, Date_Decade) on top of the raw master-table schema.

    The June-era table carried these directly; the current stage-02 schema
    keeps the source-specific columns (authors_display, genre_brit_display,
    …), so 06/07 derive them here at load time instead of stage 04 baking
    them in. Idempotent: existing columns are left untouched.
    """
    import pandas as pd

    def first_filled(*cols):
        out = pd.Series(float("nan"), index=df.index, dtype="object")
        for c in cols:
            if c in df.columns:
                out = out.fillna(df[c])
        return out

    # 06/07 do int(row["year"]): coerce bracketed catalogue dates ("[1544?]")
    # to their 4-digit year first, leaving unparseable values as NaN.
    if "year" in df.columns and df["year"].dtype == object:
        yr = pd.to_numeric(df["year"], errors="coerce")
        need = yr.isna() & df["year"].notna()
        yr.loc[need] = pd.to_numeric(
            df.loc[need, "year"].astype(str).str.extract(r"(\d{4})")[0],
            errors="coerce")
        df["year"] = yr

    # Clean play title: the raw `title` column is the title-page transcription
    # (truncated, with TCP damage glyphs: "2 The Honest Whore ~e>"). Prefer the
    # DEEP catalogue title (item_title / title.1), fall back to a de-junked
    # transcription, then the TCP id.
    def _dejunk_title(t):
        if not isinstance(t, str):
            return t
        s = t
        for _ in range(3):   # strip trailing tokens containing damage glyphs
            s2 = re.sub(r"\s+\S*[~<>«»▪〈〉\^]\S*\s*$", "", s).rstrip(" ,;·-")
            if s2 == s:
                break
            s = s2
        return s.strip() or t
    clean = first_filled("item_title", "title.1")
    if "title" in df.columns:
        clean = clean.fillna(df["title"].map(_dejunk_title))
    if "TCP" in df.columns:
        clean = clean.fillna(df["TCP"])
    df["title_raw"] = df.get("title")
    df["title"] = clean

    if "author" not in df.columns:
        df["author"] = first_filled("authors_display", "title_page_author", "Author")
        # authors_display carries numeric junk for some plays ("548")
        df.loc[df["author"].astype(str).str.fullmatch(r"\d+"), "author"] = float("nan")
    if "genre" not in df.columns:
        df["genre"] = first_filled("genre_brit_display", "genre_annals_display", "genre_wiggins")
    if "company" not in df.columns:
        df["company"] = first_filled("company_first_performance_brit_display",
                                     "company_first_performance_annals_display")
    if "play_type" not in df.columns:
        df["play_type"] = first_filled("play_type_display", "play_type_filter")
    if "Date_Decade" not in df.columns:
        yr = pd.to_numeric(df.get("year"), errors="coerce")
        dec = (yr // 10 * 10)
        df["Date_Decade"] = dec.map(lambda d: f"{int(d)}s" if pd.notna(d) else float("nan"))
    # 06/07 treat these as strings (e.g. author.split(",")); missing → ""
    for c in ("author", "genre", "company", "play_type"):
        df[c] = df[c].fillna("")
    return df


def split_facets(value, multi: bool = True) -> list[str]:
    """Split a possibly multi-valued metadata string into atomic facets.

    Catalogue fields are ';'-joined lists ("Fletcher, John; Massinger, Philip",
    "Adult Professional;Professional", "Blackfriars;Globe;Indoor Professional").
    Commas stay (they belong to "Last, First"), '/' stays ("Phoenix/Cockpit",
    "Closet/Unacted"). Uncertain-attribution markers "(?)" are stripped so
    "Queen Henrietta Maria's Men (?)" merges with its certain form.
    """
    import pandas as pd
    import re as _re
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    s = str(value).strip()
    if not s or s.lower() in ("nan", "unknown"):
        return []
    parts = s.split(";") if multi else [s]
    out = []
    for p in parts:
        p = _re.sub(r"\s*\(\?\)\s*$", "", p.strip()).strip()
        if p and p.lower() != "unknown" and p not in out:
            out.append(p)
    return out


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
