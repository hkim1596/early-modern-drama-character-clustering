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


def split_facets(value, multi: bool = True, kind: str | None = None) -> list[str]:
    """Split a possibly multi-valued metadata string into atomic facets.

    Catalogue fields are ';'-joined lists ("Fletcher, John; Massinger, Philip",
    "Adult Professional;Professional", "Blackfriars;Globe;Indoor Professional").
    Commas stay (they belong to "Last, First"), '/' stays ("Phoenix/Cockpit",
    "Closet/Unacted").

    Normalization so uncertain/contextual variants merge with their base form:
      - "(?)" markers are removed ANYWHERE ("Closet (?) Translation" →
        "Closet Translation"; "Queen Henrietta Maria's Men (?)" → certain form)
      - performance-context qualifiers "(on tour)" / "(in London)" are dropped
        (same company either way) — identity qualifiers like "(second)" are kept
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
        p = _re.sub(r"\s*\(\s*\?\s*\)", "", p)                      # any (?)
        p = _re.sub(r"\s*\((?:on tour|in London)\)", "", p, flags=_re.I)
        if kind == "author":
            # merge translator/reviser credits with the base author
            p = _re.sub(r",\s*(?:trans|rev|attrib)\.?\s*$", "", p, flags=_re.I)
        p = _re.sub(r"\s+", " ", p).strip(" ,;")
        if p and p.lower() != "unknown" and not p.isdigit() and p not in out:
            out.append(p)   # pure-digit facets are catalogue junk (e.g. "1562" as a company)
    return out


def canonical_edition_tcps(df) -> tuple[set, list[dict]]:
    """Pick ONE canonical edition per work; return (kept TCP set, report).

    The corpus contains multiple printings of the same play (All Fools ×4,
    Antonio and Mellida ×5, …). Duplicate editions inflate clusters and, worse,
    corrupt the temporal kNN genealogy: a character's nearest neighbour becomes
    its own reprint, and reprint dates masquerade as late 'followers'.

    Grouping: `work_id` where present, else normalized clean-title + author
    (i/j and u/v folded, alphanumerics only). Plays with no work_id and no
    title stand alone (kept). Within a group keep the EARLIEST edition
    (parsed year; undated last), tie-broken by most total spoken words
    (fullest transcription), then TCP id for determinism.
    """
    import pandas as pd

    def parse_year(v):
        y = pd.to_numeric(pd.Series([v]), errors="coerce").iloc[0]
        if pd.isna(y):
            m = re.search(r"(\d{4})", str(v)) if v is not None else None
            y = float(m.group(1)) if m else float("inf")
        return float(y)

    def fold(s: str) -> str:
        s = str(s).lower().replace("j", "i").replace("v", "u")
        return re.sub(r"[^a-z0-9]", "", s)

    plays = df.groupby("TCP").agg(
        work_id=("work_id", "first") if "work_id" in df.columns else ("TCP", "first"),
        item_title=("item_title", "first") if "item_title" in df.columns else ("TCP", "first"),
        title=("title", "first") if "title" in df.columns else ("TCP", "first"),
        author=("authors_display", "first") if "authors_display" in df.columns else ("TCP", "first"),
        year=("year", "first") if "year" in df.columns else ("TCP", "first"),
        words=("n_words", "sum") if "n_words" in df.columns else ("TCP", "size"),
    ).reset_index()

    def group_key(r):
        if pd.notna(r.work_id) and str(r.work_id).strip() and str(r.work_id).lower() != "nan":
            return f"w:{r.work_id}"
        t = r.item_title if (pd.notna(r.item_title) and str(r.item_title).strip()) else r.title
        if pd.isna(t) or not str(t).strip() or str(t).lower() == "nan":
            return f"solo:{r.TCP}"
        au = fold(r.author) if pd.notna(r.author) else ""
        return f"t:{fold(t)}|{au}"

    plays["_key"] = plays.apply(group_key, axis=1)
    plays["_yr"] = plays["year"].map(parse_year)

    keep: set = set()
    report: list[dict] = []
    for _, g in plays.groupby("_key"):
        g = g.sort_values(["_yr", "words", "TCP"], ascending=[True, False, True])
        keep.add(g.iloc[0]["TCP"])
        if len(g) > 1:
            report.append({
                "work": str(g.iloc[0]["item_title"] or g.iloc[0]["title"])[:60],
                "kept": g.iloc[0]["TCP"],
                "kept_year": None if g.iloc[0]["_yr"] == float("inf") else int(g.iloc[0]["_yr"]),
                "dropped": g["TCP"].tolist()[1:],
            })
    return keep, report


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
