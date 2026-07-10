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


def derive_display_columns(df, fills_path=None):
    """Add the flat display columns stages 06/07 expect (author, genre,
    company, play_type, Date_Decade) on top of the raw master-table schema.

    The June-era table carried these directly; the current stage-02 schema
    keeps the source-specific columns (authors_display, genre_brit_display,
    …), so 06/07 derive them here at load time instead of stage 04 baking
    them in. Idempotent: existing columns are left untouched.

    `fills_path` (data/manual_metadata_fills.json): Heejin-approved
    display-layer title/author/year fills for metadata-bare plays and
    corrections of mislabeled collection items (PROVENANCE_LOG Entry 005).
    Titles in the fills take precedence; author/year fill only where missing.
    Source files are never modified.
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

    # Heejin-approved manual fills/corrections (display layer only)
    if fills_path is not None and "TCP" in df.columns:
        import json as _json
        from pathlib import Path as _Path
        if _Path(fills_path).exists():
            fills = _json.load(open(fills_path, encoding="utf-8")).get("fills", {})
            t_map = {k: v["title"] for k, v in fills.items() if v.get("title")}
            a_map = {k: v["author"] for k, v in fills.items() if v.get("author")}
            y_map = {k: float(v["year"]) for k, v in fills.items() if v.get("year")}
            tcp_s = df["TCP"].astype(str)
            m = tcp_s.isin(t_map)
            df.loc[m, "title"] = tcp_s[m].map(t_map)          # fills take precedence
            if "authors_display" in df.columns:
                need_a = tcp_s.isin(a_map) & df["authors_display"].isna()
                df.loc[need_a, "authors_display"] = tcp_s[need_a].map(a_map)
            if "year" in df.columns:
                need_y = tcp_s.isin(y_map) & df["year"].isna()
                df.loc[need_y, "year"] = tcp_s[need_y].map(y_map)

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


def canonical_edition_tcps(df, prefer: set | None = None) -> tuple[set, list[dict]]:
    """Pick ONE canonical edition per work; return (kept TCP set, report).

    `prefer` is a set of TCPs that override the default choice within their
    group (e.g. New Oxford Shakespeare canonical texts from
    data/canonical_editions.json). Report entries carry every group member
    (TCP, title, year, words, characters) plus the selection policy, so
    stage 04 can write a full inclusion/exclusion record.

    The corpus contains multiple printings of the same play (All Fools ×4,
    Antonio and Mellida ×5, …). Duplicate editions inflate clusters and, worse,
    corrupt the temporal kNN genealogy: a character's nearest neighbour becomes
    its own reprint, and reprint dates masquerade as late 'followers'.

    Merging is CAST-CONFIRMED throughout — the catalogue's `work_id` proved
    unreliable (it lumps distinct plays: four different Chapman comedies share
    one work_id, and 'Antonio and Mellida ×5' mixed part 1, its sequel, and
    reprints), so no metadata key merges on its own:
      1. same folded title+author  → merge if distinctive-cast Jaccard ≥ 0.25
         (editions of one play always pass; title collisions fail)
      2. same work_id              → merge only if same title OR Jaccard ≥ 0.55
      3. metadata-bare plays (Folio/collection items: no work_id, no title,
         no year) → merge to their best cast match if J ≥ 0.5, ≥4 shared
         distinctive names, and a ≥1.5× margin over the runner-up (catches
         Folio-vs-quarto Falstaffs without confusing 1H4 with 2H4)
    Distinctive names = appearing in ≤15 plays corpus-wide. Within a group
    keep the EARLIEST edition (parsed year; undated last), tie-broken by most
    total spoken words (fullest transcription), then TCP id.
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
        chars=("TCP", "size"),
    ).reset_index()
    plays["_yr"] = plays["year"].map(parse_year)
    prefer = prefer or set()

    # distinctive casts (names in ≤15 plays: drops messenger/servant/boy,
    # keeps falstaff/hotspur/mistress quickly)
    dcast: dict[str, set] = {}
    if "normalized_name" in df.columns:
        name_play: dict[str, set] = {}
        cast: dict[str, set] = {}
        for nm, tcp in zip(df["normalized_name"].fillna("").astype(str).str.lower(),
                           df["TCP"].astype(str)):
            nm = nm.strip()
            if nm:
                name_play.setdefault(nm, set()).add(tcp)
                cast.setdefault(tcp, set()).add(nm)
        distinctive = {n for n, ps in name_play.items() if len(ps) <= 15}
        dcast = {t: (c & distinctive) for t, c in cast.items()}

    def jac(a: str, b: str) -> tuple[float, int]:
        ca, cb = dcast.get(a, set()), dcast.get(b, set())
        if not ca or not cb:
            return 0.0, 0
        inter = len(ca & cb)
        return inter / len(ca | cb), inter

    def has(v) -> bool:
        return pd.notna(v) and str(v).strip() != "" and str(v).lower() != "nan"

    tcps = plays["TCP"].tolist()
    pos = {t: i for i, t in enumerate(tcps)}
    parent = list(range(len(tcps)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: str, b: str) -> None:
        ra, rb = find(pos[a]), find(pos[b])
        if ra != rb:
            parent[rb] = ra

    def title_key(r):
        t = r.item_title if has(r.item_title) else (r.title if has(r.title) else None)
        if t is None:
            return None
        au = fold(r.author) if has(r.author) else ""
        return f"{fold(t)}|{au}"

    plays["_tk"] = [title_key(r) for r in plays.itertuples()]

    # 1) same title+author, cast-confirmed (loose: reprints always pass)
    for _, g in plays[plays["_tk"].notna()].groupby("_tk"):
        ts = g["TCP"].tolist()
        for i in range(1, len(ts)):
            j, inter = jac(ts[0], ts[i])
            small = min(len(dcast.get(ts[0], ())), len(dcast.get(ts[i], ())))
            if small < 4 or j >= 0.25:
                union(ts[0], ts[i])

    # 2) same work_id, but only cast- or title-confirmed
    if "work_id" in plays.columns:
        w = plays[plays["work_id"].map(has)]
        for _, g in w.groupby(w["work_id"].astype(str)):
            ts = g["TCP"].tolist()
            tks = g["_tk"].tolist()
            for i in range(1, len(ts)):
                same_title = tks[0] is not None and tks[0] == tks[i]
                j, inter = jac(ts[0], ts[i])
                if same_title or (j >= 0.55 and inter >= 4):
                    union(ts[0], ts[i])

    # 3) metadata-bare plays: cast matching. All candidates with J ≥ 0.55 are
    # co-editions (sequels sit near J ≈ 0.2–0.35, editions at 0.55–0.9), so a
    # margin test against the runner-up would wrongly block three-edition sets
    # (the runner-up IS another edition). A guarded best-match fallback at
    # J ≥ 0.45 catches divergent versions (bad quartos).
    bare = plays[plays["_tk"].isna() & ~plays["work_id"].map(has)]
    for b in bare.itertuples():
        bc = dcast.get(b.TCP, set())
        if len(bc) < 4:
            continue
        scored = []
        for t2 in tcps:
            if t2 == b.TCP:
                continue
            j, inter = jac(b.TCP, t2)
            if inter >= 4:
                scored.append((j, inter, t2))
        scored.sort(reverse=True)
        for j, inter, t2 in scored:
            if j >= 0.55:
                union(t2, b.TCP)
        if scored and scored[0][0] < 0.55:
            j0, i0, t0 = scored[0]
            margin_ok = (len(scored) == 1 or j0 >= 1.5 * scored[1][0]
                         or scored[1][0] >= 0.55)
            # divergent editions (bad quartos): decent J + margin
            if j0 >= 0.45 and margin_ok:
                union(t0, b.TCP)
            # heavily divergent versions (Q1 Hamlet vs Folio: renamed cast →
            # J 0.22, but 8 shared distinctive names and NO competitor)
            elif i0 >= 6 and j0 >= 0.15 and \
                    (len(scored) == 1 or j0 >= 2.5 * scored[1][0]):
                union(t0, b.TCP)

    # 4) near-identical casts under DIFFERENT titles (metadata mislabels:
    # collection items with shifted/crossed titles, e.g. a Works masque
    # carrying its neighbour's name). J ≥ 0.75 cannot be a sequel or source
    # play (those sit at 0.2–0.5), so this only merges true duplicates.
    if dcast:
        pair_inter: dict[tuple, int] = {}
        for n in distinctive:
            ps = sorted(name_play[n])
            for i in range(len(ps)):
                for j2 in range(i + 1, len(ps)):
                    pair_inter[(ps[i], ps[j2])] = pair_inter.get((ps[i], ps[j2]), 0) + 1
        for (a, b), inter in pair_inter.items():
            if inter >= 6 and a in pos and b in pos:
                j = inter / len(dcast.get(a, set()) | dcast.get(b, set()))
                if j >= 0.75:
                    union(a, b)

    plays["_grp"] = [find(pos[t]) for t in tcps]

    keep: set = set()
    report: list[dict] = []
    for _, g in plays.groupby("_grp"):
        g = g.copy()
        g["_pref"] = (~g["TCP"].isin(prefer)).astype(int)   # preferred first
        g = g.sort_values(["_pref", "_yr", "words", "TCP"],
                          ascending=[True, True, False, True])
        best = g.iloc[0]
        keep.add(best["TCP"])
        if len(g) > 1:
            work = None
            for _, r in g.iterrows():   # first titled member names the group
                if has(r["item_title"]):
                    work = r["item_title"]; break
                if work is None and has(r["title"]):
                    work = r["title"]
            work = work if work is not None else best["TCP"]
            report.append({
                "work": str(work)[:60],
                "kept": best["TCP"],
                "kept_year": None if best["_yr"] == float("inf") else int(best["_yr"]),
                "policy": "canonical-override" if best["TCP"] in prefer else "earliest-dated",
                "dropped": g["TCP"].tolist()[1:],
                "members": [{
                    "TCP": r["TCP"],
                    "title": (r["item_title"] if has(r["item_title"])
                              else (r["title"] if has(r["title"]) else "")),
                    "year": None if r["_yr"] == float("inf") else int(r["_yr"]),
                    "total_words": int(r["words"]),
                    "n_characters": int(r["chars"]),
                    "included": r["TCP"] == best["TCP"],
                } for _, r in g.iterrows()],
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
