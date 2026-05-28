"""Stage 07 — Generate the full static analysis site.

Reads cluster_xy_table__baseline.csv + cluster_labels__baseline.csv and writes
the entire browsable site into docs/ (the GitHub Pages root):

    docs/
    ├── index.html                       (landing — already exists; left alone)
    ├── interactive_clusters__*.html     (interactive maps — already exist)
    ├── cluster_evidence.html            (master index of clusters)
    ├── cluster_NN.html                  (one page per cluster)
    └── characters/<char_id>.html        (one page per character)

A scholar who clones the repo and runs the pipeline through stage 07 gets
the full site regenerated. The cluster pages list every character with
algorithmically-detected important excerpts; each character links to a deep-
dive page with the full speech text plus all metadata.

Run after stages 04 and 05:
    python code/07_generate_site.py
"""

from __future__ import annotations
import html
import re
import pandas as pd
from pathlib import Path
from collections import Counter

import config


# -------------------------------------------------------------------
# Tuning knobs
# -------------------------------------------------------------------
N_EXCERPTS_PER_CHAR_CLUSTER_PAGE = 2   # excerpts shown on the cluster page
N_EXCERPTS_PER_CHAR_DETAIL       = 5   # excerpts shown on the character page
EXCERPT_HALF_WINDOW              = 160 # characters either side of a keyword hit
TOP_CHARS_WITH_EXCERPTS_ON_CLUSTER = 40 # cap for the big residue clusters


# -------------------------------------------------------------------
# Shared CSS
# -------------------------------------------------------------------
CSS = """
:root {
  --fg: #1d1d1f; --muted: #6b6b73; --accent: #5a4a8a;
  --bg: #fafaf7; --card: #ffffff; --rule: #e5e5e0;
  --soft: #f2f2ec; --bar: #c9bfe0; --highlight: #fff3a8;
}
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
       color: var(--fg); background: var(--bg); margin: 0; padding: 0; line-height: 1.55; }
.wrap { max-width: 980px; margin: 0 auto; padding: 40px 28px 96px; }
nav.crumbs { font-size: .9rem; color: var(--muted); margin-bottom: 1em; }
nav.crumbs a { color: var(--accent); text-decoration: none; }
nav.crumbs a:hover { text-decoration: underline; }
h1 { font-size: 1.6rem; margin: 0 0 .15em; letter-spacing: -.005em; }
.lede { color: var(--muted); margin: 0 0 1.5em; }
h2 { font-size: 1.1rem; margin: 2em 0 .6em; letter-spacing: -.005em; }
h3 { font-size: 1rem; margin: 1.5em 0 .4em; }
.kvp { display: flex; flex-wrap: wrap; gap: 8px 18px; font-size: .92rem; color: var(--muted); margin-bottom: .8em; }
.kvp b { color: var(--fg); font-weight: 600; }
.tag { display: inline-block; background: var(--soft); border-radius: 10px; padding: 1px 9px; font-size: .85rem; margin: 0 4px 4px 0; }
.tag .n { color: var(--muted); margin-left: 4px; }
.bar { display: flex; align-items: center; gap: 8px; font-size: .85rem; color: var(--muted); margin: 1px 0; }
.bar .label { width: 5.5em; text-align: right; }
.bar .fill { background: var(--bar); height: 12px; border-radius: 4px; min-width: 1px; }
.bar .count { width: 3em; }
table { border-collapse: collapse; width: 100%; font-size: .9rem; margin-top: .6em; }
th, td { padding: 6px 10px; text-align: left; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { background: var(--soft); font-weight: 600; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
td a { color: var(--accent); text-decoration: none; }
td a:hover { text-decoration: underline; }
.character-block { background: var(--card); border: 1px solid var(--rule); border-radius: 6px;
                   padding: 14px 18px; margin: 16px 0; }
.character-block .ch-head { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
.character-block .ch-head .name { font-weight: 600; font-size: 1.02rem; }
.character-block .ch-head .name a { color: var(--accent); text-decoration: none; }
.character-block .ch-head .name a:hover { text-decoration: underline; }
.character-block .ch-head .meta { color: var(--muted); font-size: .9rem; text-align: right; }
.excerpt { background: var(--soft); border-left: 3px solid var(--accent);
           border-radius: 4px; padding: 8px 14px; margin: 8px 0;
           font-family: Georgia, "Times New Roman", serif; font-size: .96rem; line-height: 1.5; }
mark { background: var(--highlight); padding: 0 2px; border-radius: 2px; }
.plot { background: var(--card); border: 1px solid var(--rule); border-radius: 4px;
        padding: 12px 16px; margin: 10px 0; }
.plot .title { font-weight: 600; margin-bottom: .25em; }
.plot .meta { color: var(--muted); font-size: .88rem; margin-bottom: .5em; }
.plot .body { font-size: .94rem; }
.full-speech { background: var(--card); border: 1px solid var(--rule); border-radius: 6px;
               padding: 18px 22px; font-family: Georgia, "Times New Roman", serif;
               font-size: 1.0rem; line-height: 1.65;
               max-height: 620px; overflow-y: auto; }
.idx-card { display: block; background: var(--card); border: 1px solid var(--rule);
            border-radius: 8px; padding: 14px 18px; margin: 10px 0;
            text-decoration: none; color: inherit; }
.idx-card:hover { border-color: var(--accent); }
.idx-card h3 { margin: 0 0 .2em; color: var(--accent); font-size: 1.02rem; }
.idx-card p { margin: 0; color: var(--muted); font-size: .9rem; }
.footer { color: var(--muted); font-size: .85rem; margin-top: 3em; border-top: 1px solid var(--rule); padding-top: 1.5em; }
"""


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def esc(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    return html.escape(str(x), quote=True)


def slugify(s: str) -> str:
    """Filename-safe character id. ASCII only; preserves alphanumerics and underscore."""
    s = str(s)
    s = s.replace("::", "__")
    # Best-effort ASCII fold: drop diacritics
    import unicodedata
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("ſ", "s")
    s = re.sub(r"[^\w\-]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "untitled"


def truncate(s: str, n: int) -> str:
    if not isinstance(s, str):
        return ""
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0] + "…"


def sort_decades(values):
    known, unknown = [], []
    for v in values:
        (unknown if str(v).lower() == "unknown" else known).append(v)
    known.sort(key=lambda v: int(str(v).rstrip("s")) if str(v).rstrip("s").isdigit() else 10**9)
    return known + unknown


# -------------------------------------------------------------------
# Important-excerpt extraction
# -------------------------------------------------------------------
def _parse_top_words(s) -> list[str]:
    if not isinstance(s, str):
        return []
    return [w.strip() for w in s.split(",") if w.strip()]


def find_excerpts(speech: str, keywords: list[str], n: int) -> list[tuple[str, list[str]]]:
    """Extract up to n passages from `speech` that contain the most cluster keywords.

    Returns list of (passage, matched_keywords_in_passage). Each passage is a
    window of ~2*EXCERPT_HALF_WINDOW characters around a keyword hit, snapped
    to word boundaries and de-duplicated against earlier picks.
    """
    if not isinstance(speech, str) or not speech.strip() or not keywords:
        return []
    speech_lower = speech.lower()
    picks = []   # list of (start_idx, passage, matched_keywords)

    # For each keyword in priority order, find its first not-yet-covered occurrence
    for kw in keywords:
        kw_lc = kw.lower()
        if len(kw_lc) < 3:
            continue
        start = 0
        while True:
            idx = speech_lower.find(kw_lc, start)
            if idx == -1:
                break
            # Is this position inside an already-chosen window?
            if any(abs(idx - p[0]) < EXCERPT_HALF_WINDOW for p in picks):
                start = idx + len(kw_lc)
                continue
            # Build window, snap to word boundaries
            lo = max(0, idx - EXCERPT_HALF_WINDOW)
            hi = min(len(speech), idx + len(kw_lc) + EXCERPT_HALF_WINDOW)
            while lo > 0 and not speech[lo - 1].isspace():
                lo -= 1
            while hi < len(speech) and not speech[hi].isspace():
                hi += 1
            passage = speech[lo:hi].strip()
            # Collect ALL cluster keywords that appear in this passage
            passage_lc = passage.lower()
            hits = [k for k in keywords if k.lower() in passage_lc and len(k) >= 3]
            picks.append((idx, passage, hits))
            if len(picks) >= n:
                break
            start = idx + len(kw_lc)
        if len(picks) >= n:
            break

    # Re-rank picks by number of distinct keywords matched (then by appearance order)
    picks.sort(key=lambda t: (-len(set(t[2])), t[0]))
    return [(p, h) for _, p, h in picks[:n]]


def highlight_keywords(text: str, keywords: list[str]) -> str:
    """HTML-escape `text` and wrap occurrences of `keywords` in <mark>."""
    if not text:
        return ""
    escaped = esc(text)
    # Build a pattern that matches any keyword as a whole word, case-insensitive
    if not keywords:
        return escaped
    pat = re.compile(
        r"\b(" + "|".join(re.escape(k) for k in sorted(set(keywords), key=len, reverse=True)) + r")\b",
        re.IGNORECASE,
    )
    return pat.sub(lambda m: f"<mark>{m.group(0)}</mark>", escaped)


# -------------------------------------------------------------------
# Renderers
# -------------------------------------------------------------------
def cluster_label_for(cluster_id: int, df: pd.DataFrame) -> str:
    sub = df[df.cluster == cluster_id]
    if "topic_label" in sub.columns and sub["topic_label"].notna().any():
        return str(sub["topic_label"].iloc[0])
    return f"Cluster {cluster_id}"


def render_meta_line(row: pd.Series) -> str:
    """One-liner with author / date / genre / company / theater."""
    parts = []
    if isinstance(row.get("author"), str) and row["author"].strip():
        parts.append(esc(row["author"]))
    if pd.notna(row.get("year")):
        parts.append(str(int(row["year"])))
    if isinstance(row.get("genre"), str) and row["genre"].strip():
        parts.append(esc(row["genre"]))
    if isinstance(row.get("company"), str) and row["company"].strip():
        parts.append(esc(row["company"]))
    if isinstance(row.get("theater"), str) and row["theater"].strip():
        parts.append(esc(row["theater"]))
    return " · ".join(parts)


def render_decade_bars(decade_counts: dict) -> str:
    if not decade_counts:
        return "<p><em>No dated plays in this cluster.</em></p>"
    max_n = max(decade_counts.values())
    rows = []
    for d in sort_decades(list(decade_counts.keys())):
        n = decade_counts[d]
        w = max(1, int(round(220 * n / max_n)))
        rows.append(
            f'<div class="bar"><div class="label">{esc(d)}</div>'
            f'<div class="fill" style="width:{w}px"></div>'
            f'<div class="count">{n}</div></div>'
        )
    return "\n".join(rows)


def render_author_tags(author_counts: pd.Series, limit: int = 18) -> str:
    tags = []
    for au, n in author_counts.head(limit).items():
        label = au if (isinstance(au, str) and au.strip()) else "(unknown)"
        tags.append(f'<span class="tag">{esc(label)}<span class="n">{n}</span></span>')
    if len(author_counts) > limit:
        tags.append(f'<span class="tag">+{len(author_counts) - limit} more</span>')
    return "\n".join(tags)


def render_character_block_for_cluster_page(row: pd.Series, keywords: list[str]) -> str:
    """Block rendered inside a cluster page: header + 2 excerpts + 'full' link."""
    char_id = row.get("character_id", "")
    slug = slugify(char_id)
    display = row.get("display_name") or row.get("normalized_name") or "?"
    raw = row.get("raw_names", "")
    play = row.get("title", "")
    meta = render_meta_line(row)
    role = row.get("role_description", "")
    n_words = "" if pd.isna(row.get("n_words")) else int(row["n_words"])

    excerpts = find_excerpts(row.get("speech_text", "") or "",
                             keywords, N_EXCERPTS_PER_CHAR_CLUSTER_PAGE)
    if excerpts:
        ex_html = "\n".join(
            f'<div class="excerpt">{highlight_keywords(p, hits)}</div>'
            for p, hits in excerpts
        )
    else:
        ex_html = ('<div class="excerpt"><em>No keyword-matching excerpt found; '
                   'see the full speech on the character page.</em></div>')

    return f"""
<div class="character-block">
  <div class="ch-head">
    <div class="name"><a href="characters/{slug}.html">{esc(display)}</a>
      <span class="muted"> in <em>{esc(play)}</em></span>
    </div>
    <div class="meta">{meta}<br>{n_words} words</div>
  </div>
  {f'<div class="muted" style="color:var(--muted); font-size:.9rem; margin-top:.2em">Role: {esc(truncate(role, 240))}</div>' if isinstance(role, str) and role.strip() else ''}
  {ex_html}
  <div style="font-size:.88rem; margin-top:.4em">
    <a href="characters/{slug}.html">→ View full speech and metadata</a>
    {f'<span class="muted" style="color:var(--muted)"> · speech prefix(es): {esc(raw)}</span>' if isinstance(raw, str) and raw and raw != display else ''}
  </div>
</div>
"""


def render_cluster_page(cluster_id: int, df: pd.DataFrame, labels: pd.DataFrame) -> str:
    sub = df[df.cluster == cluster_id].copy().sort_values("n_words", ascending=False).reset_index(drop=True)
    n = len(sub)
    label = cluster_label_for(cluster_id, df)
    top_words_str = labels.loc[cluster_id, "top_words"] if cluster_id in labels.index else ""
    keywords = _parse_top_words(top_words_str)

    author_counts = (
        sub["author"].fillna("(unknown)").astype(str)
        .str.split(",").str[0].str.strip()
        .value_counts()
    )
    decade_counts = sub["Date_Decade"].fillna("Unknown").astype(str).value_counts().to_dict()

    title = f"Cluster {cluster_id} — {label}"

    # Top-N characters with excerpts inline
    top_for_excerpts = sub.head(TOP_CHARS_WITH_EXCERPTS_ON_CLUSTER)
    excerpt_blocks = "\n".join(
        render_character_block_for_cluster_page(r, keywords) for _, r in top_for_excerpts.iterrows()
    )

    # Full table of every character (sortable)
    table_rows = []
    for _, r in sub.iterrows():
        slug = slugify(r.get("character_id", ""))
        nm = esc(r.get("display_name") or "?")
        play = esc(r.get("title", ""))
        au = esc((r.get("author") or "").split(",")[0])
        yr = "" if pd.isna(r.get("year")) else int(r["year"])
        gn = esc(r.get("genre", ""))
        co = esc(r.get("company", ""))
        nw = "" if pd.isna(r.get("n_words")) else int(r["n_words"])
        table_rows.append(
            f"<tr><td><a href='characters/{slug}.html'>{nm}</a></td>"
            f"<td>{play}</td><td>{au}</td><td class='num'>{yr}</td>"
            f"<td>{gn}</td><td>{co}</td><td class='num'>{nw}</td></tr>"
        )
    table_html = (
        "<table><thead><tr>"
        "<th>Character</th><th>Play</th><th>Author</th><th>Year</th>"
        "<th>Genre</th><th>Company</th><th>Words</th>"
        "</tr></thead><tbody>"
        + "".join(table_rows) + "</tbody></table>"
    )

    # Plot summaries
    plays = sub.drop_duplicates("TCP").sort_values("year", na_position="last")
    plot_blocks = []
    for _, r in plays.iterrows():
        plot = truncate(r.get("plot", "") or "", 1500)
        if not plot:
            continue
        meta = render_meta_line(r)
        plot_blocks.append(
            f'<div class="plot"><div class="title">{esc(r.get("title", ""))}</div>'
            f'<div class="meta">{meta}</div>'
            f'<div class="body">{esc(plot)}</div></div>'
        )
    plot_html = "\n".join(plot_blocks) if plot_blocks else "<p><em>No plot summaries available.</em></p>"

    overflow_note = ""
    if n > TOP_CHARS_WITH_EXCERPTS_ON_CLUSTER:
        overflow_note = (
            f'<p class="lede" style="margin-top:.4em">Showing important excerpts for the '
            f'{TOP_CHARS_WITH_EXCERPTS_ON_CLUSTER} longest characters; '
            f'the full speeches of all {n} are on the individual character pages linked below.</p>'
        )

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Character Clustering</title>
<style>{CSS}</style>
</head><body><div class="wrap">

<nav class="crumbs">
  <a href="index.html">Home</a> ›
  <a href="cluster_evidence.html">All clusters</a> ›
  <span>Cluster {cluster_id}</span>
</nav>

<h1>{esc(title)}</h1>
<p class="lede">Each character is shown with two algorithmically-selected
excerpts containing the cluster's distinguishing words (highlighted). Click any
character's name to open their full-speech page.</p>

<div class="kvp">
  <span><b>{n}</b> characters</span>
  <span><b>{len(author_counts)}</b> authors</span>
  <span><b>{sub['TCP'].nunique()}</b> plays</span>
  <span>Distinguishing words: <b>{esc(top_words_str)}</b></span>
</div>

<h2>Authorship</h2>
{render_author_tags(author_counts)}

<h2>Decade distribution</h2>
{render_decade_bars(decade_counts)}

<h2>Characters with important excerpts</h2>
{overflow_note}
{excerpt_blocks}

<h2>All {n} characters in this cluster</h2>
{table_html}

<h2>Plot summaries for plays represented</h2>
{plot_html}

<div class="footer">
  Generated automatically from <code>cluster_xy_table__baseline.csv</code> by
  <code>code/07_generate_site.py</code>. View the
  <a href="https://github.com/hkim1596/early-modern-drama-character-clustering">source on GitHub</a>.
</div>
</div></body></html>"""


def render_character_page(row: pd.Series, df: pd.DataFrame, labels: pd.DataFrame) -> str:
    """Per-character deep-dive page: full speech + all metadata + excerpts."""
    cluster_id = int(row["cluster"]) if pd.notna(row["cluster"]) else -1
    label = cluster_label_for(cluster_id, df) if cluster_id != -1 else "Outlier"
    top_words_str = labels.loc[cluster_id, "top_words"] if cluster_id in labels.index else ""
    keywords = _parse_top_words(top_words_str)
    speech = row.get("speech_text", "") or ""

    display = row.get("display_name") or row.get("normalized_name") or "?"
    play    = row.get("title", "")
    author  = row.get("author", "")
    year    = "" if pd.isna(row.get("year")) else int(row["year"])
    decade  = row.get("Date_Decade", "")
    genre   = row.get("genre", "")
    play_t  = row.get("play_type", "")
    company = row.get("company", "")
    theater = row.get("theater", "")
    role    = row.get("role_description", "")
    raw     = row.get("raw_names", "")
    n_words = "" if pd.isna(row.get("n_words")) else int(row["n_words"])
    n_chars = "" if pd.isna(row.get("n_chars")) else int(row["n_chars"])

    # Metadata table — every available field
    meta_rows = []
    for label_text, val in [
        ("Play",            play),
        ("Author",          author),
        ("Year",            year),
        ("Decade",          decade),
        ("Genre",           genre),
        ("Play type",       play_t),
        ("Company",         company),
        ("Theater",         theater),
        ("Role description", role),
        ("Speech prefix(es)", raw),
        ("Words",           n_words),
        ("Characters",      n_chars),
        ("TCP id",          row.get("TCP", "")),
        ("BritDrama no.",   "" if pd.isna(row.get("brit_drama_number")) else row.get("brit_drama_number")),
        ("Cluster",         f"Cluster {cluster_id} — {label}" if cluster_id != -1 else "Outlier (no cluster)"),
    ]:
        if val == "" or pd.isna(val if not isinstance(val, str) else None):
            continue
        if isinstance(val, str) and not val.strip():
            continue
        meta_rows.append(f"<tr><th>{esc(label_text)}</th><td>{esc(val)}</td></tr>")
    meta_html = "<table>" + "\n".join(meta_rows) + "</table>"

    # Important excerpts
    excerpts = find_excerpts(speech, keywords, N_EXCERPTS_PER_CHAR_DETAIL)
    if excerpts and cluster_id != -1:
        ex_intro = (f"Passages from this character's speech that contain the most "
                    f"distinguishing words for Cluster {cluster_id} "
                    f"(<em>{esc(', '.join(keywords[:6]))}…</em>). Matches are highlighted.")
        ex_html = "\n".join(
            f'<div class="excerpt">{highlight_keywords(p, hits)}</div>'
            for p, hits in excerpts
        )
    else:
        ex_intro = ("No keyword-matching excerpt could be extracted (the cluster label "
                    "doesn't share vocabulary with this character's speech).")
        ex_html = ""

    # Full speech with light formatting (just line breaks)
    full_speech_html = esc(speech) if speech else "<em>No speech text available.</em>"

    # Plot summary
    plot = truncate(row.get("plot", "") or "", 2500)
    plot_html = f'<div class="plot"><div class="title">Plot — {esc(play)}</div><div class="body">{esc(plot)}</div></div>' if plot else ""

    cluster_link = (f'<a href="cluster_{cluster_id:02d}.html">Cluster {cluster_id} — {esc(label)}</a>'
                    if cluster_id != -1 else "<em>outlier (no cluster)</em>")

    title = f"{display} in {play}"
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Character Clustering</title>
<style>{CSS}</style>
</head><body><div class="wrap">

<nav class="crumbs">
  <a href="../index.html">Home</a> ›
  <a href="../cluster_evidence.html">All clusters</a> ›
  {cluster_link} ›
  <span>{esc(display)}</span>
</nav>

<h1>{esc(display)}</h1>
<p class="lede">in <em>{esc(play)}</em>{(' — ' + esc(author)) if isinstance(author, str) and author.strip() else ''}</p>

<h2>Metadata</h2>
{meta_html}

<h2>Important excerpts</h2>
<p class="lede" style="font-size:.92rem; margin-top:-.5em">{ex_intro}</p>
{ex_html}

<h2>Full speech</h2>
<div class="full-speech">{full_speech_html}</div>

{('<h2>Plot summary</h2>' + plot_html) if plot_html else ''}

<div class="footer">
  Generated automatically from <code>cluster_xy_table__baseline.csv</code>.
  View other characters in this group on the
  {cluster_link} page.
</div>
</div></body></html>"""


def render_master_index(df: pd.DataFrame, labels: pd.DataFrame) -> str:
    cards = []
    for cid in sorted(c for c in df.cluster.unique() if c != -1):
        sub = df[df.cluster == cid]
        n = len(sub)
        top_words = labels.loc[cid, "top_words"] if cid in labels.index else ""
        author_counts = (
            sub["author"].fillna("(unknown)").astype(str).str.split(",").str[0].str.strip().value_counts()
        )
        years = sub["year"].dropna()
        yr_str = f"{int(years.min())}–{int(years.max())}, median {int(years.median())}" if len(years) else ""
        cards.append(f"""
<a class="idx-card" href="cluster_{cid:02d}.html">
  <h3>Cluster {cid} — {esc(cluster_label_for(cid, df))}</h3>
  <p>{n} characters · {len(author_counts)} authors · {yr_str}<br>
     <small>{esc(top_words)}</small></p>
</a>""")

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>All clusters · Character Clustering</title>
<style>{CSS}</style>
</head><body><div class="wrap">

<nav class="crumbs"><a href="index.html">Home</a> › <span>All clusters</span></nav>
<h1>Per-cluster evidence</h1>
<p class="lede">Each cluster's full character list, important speech excerpts, decade
distribution, authorial mix, and the plot summaries of every play represented.
Click into a cluster, then any character's name, to read their full speech with metadata.</p>

{''.join(cards)}

<div class="footer">
  Generated automatically by <code>code/07_generate_site.py</code>.
</div>
</div></body></html>"""


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
def main() -> None:
    cxy = config.DATA_DIR / "cluster_xy_table__baseline.csv"
    if not cxy.exists():
        raise FileNotFoundError(f"{cxy} not found. Run 04_cluster.py first.")
    df = pd.read_csv(cxy)
    df["cluster"] = df["cluster"].astype(int)

    lbl_path = config.DATA_DIR / "cluster_labels__baseline.csv"
    if lbl_path.exists():
        labels = pd.read_csv(lbl_path).set_index("cluster")
    else:
        labels = pd.DataFrame(columns=["top_words"]).set_index(pd.Index([], name="cluster"))

    out_dir = config.RESULTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    chars_dir = out_dir / "characters"
    chars_dir.mkdir(parents=True, exist_ok=True)

    # 1) cluster pages (non-outlier clusters only)
    clusters = sorted(c for c in df.cluster.unique() if c != -1)
    for cid in clusters:
        (out_dir / f"cluster_{cid:02d}.html").write_text(
            render_cluster_page(cid, df, labels), encoding="utf-8"
        )
    print(f"✅ {len(clusters)} cluster pages written")

    # 2) master cluster index
    (out_dir / "cluster_evidence.html").write_text(
        render_master_index(df, labels), encoding="utf-8"
    )
    print(f"✅ cluster_evidence.html written")

    # 3) character pages (only for characters in non-outlier clusters)
    clustered = df[df.cluster != -1].copy()
    n_written = 0
    for _, row in clustered.iterrows():
        slug = slugify(row.get("character_id", ""))
        page = render_character_page(row, df, labels)
        (chars_dir / f"{slug}.html").write_text(page, encoding="utf-8")
        n_written += 1
    print(f"✅ {n_written} character pages written to {chars_dir}")

    print(f"\n📂 Site is at: {out_dir}")
    print(f"   Open {out_dir}/index.html locally, or push to GitHub Pages.")


if __name__ == "__main__":
    main()
