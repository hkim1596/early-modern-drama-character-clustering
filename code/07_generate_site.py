"""Stage 07 — Generate the full static analysis site.

Reads cluster_xy_table__<CLUSTER_TABLES[0]>.csv + its cluster_labels file and writes
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
th.sortable { cursor: pointer; user-select: none; }
th.sortable:hover { background: #e8e8df; }
th.sortable::after { content: " ↕"; color: var(--muted); font-size: .8em; }
.badge { display: inline-block; font-size: .72rem; font-weight: 600; color: #7a6a2e;
         background: #f5eecb; border-radius: 8px; padding: 0 7px; margin-left: 6px; vertical-align: 1px; }
.landmarks { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; margin: .6em 0 1em; }
.lm-card { background: var(--card); border: 1px solid var(--rule); border-radius: 8px; padding: 10px 14px; font-size: .9rem; }
.lm-card .who { font-weight: 600; }
.lm-card .who a { color: var(--accent); text-decoration: none; }
.lm-card .who a:hover { text-decoration: underline; }
.lm-card .whence { color: var(--muted); font-size: .86rem; }
details { margin: 1em 0; }
details > summary { cursor: pointer; font-weight: 600; font-size: 1.05rem; padding: .3em 0; }
h2.fam { margin-top: 2.2em; border-bottom: 1px solid var(--rule); padding-bottom: .3em; }
.fam-desc { color: var(--muted); font-size: .9rem; margin: .2em 0 .6em; }
.banner { background: #f4f1fa; border: 1px solid #ddd3ee; border-radius: 8px;
          padding: 10px 16px; font-size: .9rem; margin: 0 0 1.4em; color: #3f3f46; }
.banner b { color: var(--fg); }
.badge-prop { background: #fde8d7; color: #8a5a2e; }
.prop-mark { display: inline-block; font-size: .7rem; font-weight: 600; color: #8a5a2e;
             background: #fde8d7; border-radius: 8px; padding: 0 6px; margin-left: 6px; vertical-align: 2px; }
.kw-caveat { color: var(--muted); font-size: .84rem; margin: -.9em 0 1.2em; }
.chip { display: inline-block; font-size: .72rem; font-weight: 600; color: #4a5a7a;
        background: #e3eaf6; border-radius: 8px; padding: 0 7px; margin-left: 6px; vertical-align: 1px; }
.tstrip { display: flex; align-items: flex-end; gap: 2px; height: 56px; margin: .5em 0 .15em; }
.tslot { position: relative; width: 9px; height: 52px; }
.tslot .c1 { position: absolute; bottom: 0; left: 0; width: 4px; background: #d9d9d0; border-radius: 1px; }
.tslot .c2 { position: absolute; bottom: 0; right: 0; width: 4px; background: var(--accent);
             border-radius: 1px; opacity: .85; }
.taxis { font-size: .75rem; color: var(--muted); margin-bottom: .6em; }
.sig-group { margin: .25em 0 .5em; }
.sig-group .glabel { display: inline-block; min-width: 7.5em; color: var(--muted);
                     font-size: .85rem; vertical-align: top; }
.curated { background: #fbf7ee; border: 1px solid #eadfc8; border-radius: 8px;
           padding: 10px 16px; margin: 0 0 1.2em; font-size: .93rem; }
.curated .clabel { font-weight: 600; font-size: .78rem; letter-spacing: .02em;
                   color: #7a6a2e; text-transform: uppercase; margin-right: .5em; }
.spark { display: inline-flex; align-items: flex-end; gap: 1px; height: 14px; margin-left: 8px; }
.spark i { display: inline-block; width: 3px; background: var(--bar); }
"""

# Authors whose plays general readers are most likely to know — used to pick
# "familiar landmarks" per cluster (never affects the clustering itself).
FAMILIAR_AUTHORS = {"Shakespeare", "Jonson", "Marlowe", "Middleton", "Fletcher",
                    "Webster", "Kyd", "Ford", "Massinger", "Beaumont", "Dekker",
                    "Chapman", "Heywood", "Marston", "Shirley", "Lyly", "Greene"}


def load_cluster_meta() -> dict:
    """Curated names/families from data/cluster_names__<name>.json (optional)."""
    path = config.DATA_DIR / f"cluster_names__{config.CLUSTER_TABLES[0]}.json"
    if not path.exists():
        return {}
    import json as _json
    with open(path, encoding="utf-8") as f:
        return {int(k): v for k, v in _json.load(f).get("clusters", {}).items()}


def load_cluster_meta_top() -> dict:
    """Whole cluster_names JSON (top-level optional keys: families, attested_types)."""
    path = config.DATA_DIR / f"cluster_names__{config.CLUSTER_TABLES[0]}.json"
    if not path.exists():
        return {}
    import json as _json
    with open(path, encoding="utf-8") as f:
        return _json.load(f)


def load_cluster_summary() -> dict:
    """Run parameters + audited stats from data/cluster_summary__<name>.json."""
    path = config.DATA_DIR / f"cluster_summary__{config.CLUSTER_TABLES[0]}.json"
    if not path.exists():
        return {}
    import json as _json
    with open(path, encoding="utf-8") as f:
        return _json.load(f)


# -------------------------------------------------------------------
# Tier-1 evidence-page update (2026-07-10, PROVENANCE_LOG Entry 006)
# -------------------------------------------------------------------
# Partition identity shown in the reading-guidance banner. Update when the
# partition changes (ids reshuffle on every stage-04 re-run).
PARTITION_NOTE = "2026-07-07 NOS-verified run"
# Seed-to-seed stability is not recorded in cluster_summary__*.json; the value
# is from Clustering_Results_Report_2026-07-08 (5 refits: ARI 0.292,
# range 0.260–0.345). Re-measure and update after any re-cluster.
SEED_ARI_TEXT = "seed-to-seed ARI 0.29 (0.26–0.35 over 5 refits; report 2026-07-08)"

# Historical-profile badge rules (documented in PROVENANCE_LOG Entry 006):
# a cluster is badged from its DATED members only, and only if ≥20 are dated.
#   early-rooted : pre-1590 share ≥ 1.4 × the corpus pre-1590 share
#   late register: post-1625 share ≥ 1.15 × corpus AND median year > corpus median
# On the 2026-07-07 partition these rules reproduce the report's early
# (cl2/15/22/11) and late (cl20/19/4) lists.
BADGE_EARLY_LIFT = 1.40
BADGE_LATE_LIFT  = 1.15
MIN_DATED_FOR_BADGES = 20

# Signature panels: minimum members carrying a facet before a lift is shown,
# and the minimum lift that counts as a signature.
SIG_MIN_N = {"author": 4, "genre": 5, "company": 5, "theater": 5, "play_type": 5}
SIG_MIN_LIFT = 1.2
SIG_TOP = 5


def render_reading_banner(summary: dict) -> str:
    """RQ1/RQ30 framing + partition identity (proposal item 1.1)."""
    k    = summary.get("k", "?")
    n    = summary.get("n_clustered")
    seed = summary.get("random_state", "?")
    sil  = summary.get("silhouette_cosine_full")
    n_s  = f"{n:,}" if isinstance(n, int) else "?"
    sil_s = f"{sil:.3f}" if isinstance(sil, (int, float)) else "?"
    return (f'<div class="banner"><b>How to read these pages.</b> '
            f'Partition: {PARTITION_NOTE} (k={k}, seed {seed}, {n_s} characters). '
            f'Character-space is a <b>continuum with dense prototype regions</b>, not a set of '
            f'discrete boxes (silhouette {sil_s}; {SEED_ARI_TEXT}): read each cluster as a '
            f'density peak, membership as graded, and low-typicality members as blends of '
            f'several regions. Cluster ids are not stable across re-clustering runs.</div>')


def _analysis_years(frame: pd.DataFrame) -> pd.Series:
    """Year series used for the historical profile: the performance year as
    recorded in the master table (numeric + 4-digit extraction), WITHOUT the
    Entry-005 display-layer fill years (parent-volume print years, late-
    skewed). This reproduces the report's dated base exactly (n=6,040,
    median 1611, pre-1590 8.6%, post-1625 31.8% on the 2026-07-07 partition);
    the roster/landmark 'Year' columns keep the display year."""
    col = "year_analysis" if "year_analysis" in frame.columns else "year"
    return frame[col].dropna().astype(int)


def corpus_context(df: pd.DataFrame) -> dict:
    """Corpus-wide baselines (clustered characters only) shared by all pages:
    5-year-bin date shares, median/pre-1590/post-1625, and facet base rates."""
    from utils import split_facets
    cl = df[df.cluster >= 0]
    dated = _analysis_years(cl)
    bin_of = lambda y: int(y) // 5 * 5
    bins = sorted({bin_of(y) for y in dated})
    bin_counts = Counter(bin_of(y) for y in dated)
    nd = len(dated)

    facet_base: dict[str, Counter] = {}
    facet_known: dict[str, int] = {}
    for col, kind in [("author", "author"), ("genre", None), ("company", None),
                      ("theater", None), ("play_type", None)]:
        c: Counter = Counter()
        known = 0
        if col in cl.columns:
            for v in cl[col]:
                f = set(split_facets(v, kind=kind))
                if f:
                    known += 1
                    c.update(f)
        facet_base[col] = c
        facet_known[col] = known

    return {
        "n": len(cl),
        "dated_n": nd,
        "median": int(dated.median()) if nd else None,
        "pre_share": float((dated < 1590).mean()) if nd else 0.0,
        "post_share": float((dated > 1625).mean()) if nd else 0.0,
        "bins": bins,
        "bin_share": {b: bin_counts[b] / nd for b in bins} if nd else {},
        "facet_base": facet_base,
        "facet_known": facet_known,
    }


def render_temporal_strip(sub: pd.DataFrame, ctx: dict) -> tuple[str, list[str]]:
    """Historical profile (proposal item 1.3): paired 5-year-bin share bars
    (cluster vs corpus), headline stats, and early/late badges per the rules
    above. Returns (html, badge_names)."""
    dated = _analysis_years(sub)
    nd, n = len(dated), len(sub)
    if nd < 10:
        return (f"<p class='lede' style='font-size:.92rem'><em>Only {nd} of {n} members "
                f"are dated — temporal profile omitted.</em></p>", [])

    med = int(dated.median())
    pre, post = float((dated < 1590).mean()), float((dated > 1625).mean())
    cmed, cpre, cpost = ctx["median"], ctx["pre_share"], ctx["post_share"]
    pre_lift  = pre / cpre if cpre else float("nan")
    post_lift = post / cpost if cpost else float("nan")

    badges = []
    if nd >= MIN_DATED_FOR_BADGES and pre_lift >= BADGE_EARLY_LIFT:
        badges.append("early-rooted")
    if nd >= MIN_DATED_FOR_BADGES and post_lift >= BADGE_LATE_LIFT and med > cmed:
        badges.append("late register")

    bin_of = lambda y: int(y) // 5 * 5
    counts = Counter(bin_of(y) for y in dated)
    shares = {b: counts.get(b, 0) / nd for b in ctx["bins"]}
    max_share = max(max(shares.values(), default=0.0),
                    max(ctx["bin_share"].values(), default=0.0)) or 1.0
    slots = []
    for b in ctx["bins"]:
        cs, ks = ctx["bin_share"].get(b, 0.0), shares.get(b, 0.0)
        h1 = max(1, round(50 * cs / max_share))
        h2 = max(1 if counts.get(b, 0) else 0, round(50 * ks / max_share))
        lift = (ks / cs) if cs else float("nan")
        tip = (f"{b}–{b+4}: {counts.get(b, 0)} member(s), {ks:.1%} of cluster "
               f"(corpus {cs:.1%}" + (f", ×{lift:.1f}" if cs else "") + ")")
        slots.append(f'<div class="tslot" title="{esc(tip)}">'
                     f'<div class="c1" style="height:{h1}px"></div>'
                     + (f'<div class="c2" style="height:{h2}px"></div>' if h2 else "")
                     + '</div>')
    axis = (f'<div class="taxis">{ctx["bins"][0]}–{ctx["bins"][-1] + 4} in 5-year bins · '
            f'<span style="color:var(--accent)">▮</span> this cluster vs '
            f'<span style="color:#b7b7ac">▮</span> corpus (share of dated members; hover for '
            f'numbers). Performance years as catalogued; the display-only fill years of '
            f'PROVENANCE_LOG Entry 005 are excluded here, so a member can show a year in the '
            f'roster yet not count as dated above.</div>')

    stats = (f'<div class="kvp">'
             f'<span><b>{nd}</b> dated of {n}</span>'
             f'<span>median <b>{med}</b> (corpus {cmed})</span>'
             f'<span>pre-1590 <b>{pre:.0%}</b> (corpus {cpre:.0%}, ×{pre_lift:.1f})</span>'
             f'<span>post-1625 <b>{post:.0%}</b> (corpus {cpost:.0%}, ×{post_lift:.1f})</span>'
             f'</div>')
    return (stats + f'<div class="tstrip">{"".join(slots)}</div>' + axis, badges)


def render_signature_panel(sub: pd.DataFrame, ctx: dict) -> str:
    """Signatures as lift vs the clustered corpus (proposal item 1.4):
    share-of-members-carrying-facet in cluster ÷ same share in corpus."""
    from utils import split_facets
    n_sub, n_corpus = len(sub), ctx["n"]
    groups = [("Authors", "author", "author"), ("Genres", "genre", None),
              ("Companies", "company", None), ("Theaters", "theater", None),
              ("Play types", "play_type", None)]
    out = []
    for label, col, kind in groups:
        if col not in sub.columns:
            continue
        c: Counter = Counter()
        known = 0
        for v in sub[col]:
            f = set(split_facets(v, kind=kind))
            if f:
                known += 1
                c.update(f)
        base = ctx["facet_base"][col]
        rows = []
        for facet, cn in c.items():
            if cn < SIG_MIN_N[col]:
                continue
            bn = base.get(facet, 0)
            if not bn:
                continue
            lift = (cn / n_sub) / (bn / n_corpus)
            if lift >= SIG_MIN_LIFT:
                rows.append((lift, cn, facet))
        rows.sort(reverse=True)
        if rows:
            tags = "".join(f'<span class="tag">{esc(f)} ×{l:.1f}<span class="n">n={cn}</span></span>'
                           for l, cn, f in rows[:SIG_TOP])
        else:
            tags = '<span class="tag" style="color:var(--muted)">no strong signature</span>'
        cov = ""
        if known / n_sub < 0.9:
            cov = (f' <span style="color:var(--muted); font-size:.82rem">'
                   f'(known for {known / n_sub:.0%} of members)</span>')
        out.append(f'<div class="sig-group"><span class="glabel">{label}</span> {tags}{cov}</div>')
    note = ('<p class="lede" style="font-size:.88rem">×lift = share of this cluster\'s members '
            f'with the facet ÷ the same share over all {n_corpus:,} clustered characters '
            f'(only facets carried by ≥{SIG_MIN_N["genre"]} members, lift ≥ {SIG_MIN_LIFT}, top {SIG_TOP} shown; '
            f'authors ≥{SIG_MIN_N["author"]}). Raw counts are in the collapsed list below.</p>')
    return note + "".join(out)


def render_curated_block(entry: dict) -> str:
    """Curated interpretation (proposal item 1.5): optional per-cluster fields
    historical_types / note / criticism in cluster_names__<name>.json."""
    if not entry:
        return ""
    types = entry.get("historical_types") or []
    note  = (entry.get("note") or "").strip()
    crit  = (entry.get("criticism") or "").strip()
    if not (types or note or crit):
        return ""
    parts = []
    if types:
        tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in types)
        parts.append(f'<div><span class="clabel">Historical identifications</span> {tags}</div>')
    if note:
        parts.append(f'<div style="margin-top:.35em">{esc(note)}</div>')
    if crit:
        parts.append(f'<div style="margin-top:.35em"><span class="clabel">Criticism hooks</span> '
                     f'{esc(crit)}</div>')
    return f'<div class="curated">{"".join(parts)}</div>'


def render_name_badge(entry: dict) -> str:
    """Name-status marker (proposal item 1.2): assistant-proposed names stay
    visibly provisional until Heejin revises them (PROVENANCE_LOG Entry 004)."""
    if not entry or "proposed" not in entry:
        return ""
    return (f'<span class="badge badge-prop" title="{esc(entry["proposed"])}">'
            f'name proposed — pending curation</span>')


def render_decade_spark(sub: pd.DataFrame) -> str:
    """Tiny inline decade sparkline for index cards (proposal item 1.7)."""
    counts = sub["Date_Decade"].dropna().astype(str).value_counts()
    counts = counts[~counts.index.str.lower().str.startswith("unknown")]
    if counts.empty:
        return ""
    decades = sort_decades(list(counts.index))
    mx = counts.max()
    bars = "".join(f'<i style="height:{max(2, round(13 * counts[d] / mx))}px"></i>'
                   for d in decades)
    return f'<span class="spark" title="decades {esc(decades[0])}–{esc(decades[-1])}">{bars}</span>'


SORT_JS = """
<script>
document.querySelectorAll("table.sortable th").forEach(function (th, ci) {
  th.classList.add("sortable");
  th.addEventListener("click", function () {
    var tb = th.closest("table").querySelector("tbody");
    var rows = Array.from(tb.querySelectorAll("tr"));
    var dir = th.dataset.dir === "asc" ? -1 : 1;
    th.dataset.dir = dir === 1 ? "asc" : "desc";
    rows.sort(function (a, b) {
      var x = a.children[ci].dataset.v ?? a.children[ci].textContent.trim();
      var y = b.children[ci].dataset.v ?? b.children[ci].textContent.trim();
      var nx = parseFloat(x), ny = parseFloat(y);
      if (!isNaN(nx) && !isNaN(ny)) return (nx - ny) * dir;
      if (x === "" && y !== "") return 1;
      if (y === "" && x !== "") return -1;
      return x.localeCompare(y) * dir;
    });
    rows.forEach(function (r) { tb.appendChild(r); });
  });
});
</script>
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


def render_character_block_for_cluster_page(row: pd.Series, keywords: list[str],
                                            why: list[str] | None = None) -> str:
    """Block rendered inside a cluster page: header + 2 excerpts + 'full' link.
    `why` = which landmark set(s) selected this member (typical/early/familiar),
    rendered as chips so the excerpt section explains its own sampling (item 1.6a)."""
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

    chips = "".join(f'<span class="chip">{esc(w)}</span>' for w in (why or []))
    return f"""
<div class="character-block">
  <div class="ch-head">
    <div class="name"><a href="characters/{slug}.html">{esc(display)}</a>
      <span class="muted"> in <em>{esc(play)}</em></span>{chips}
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


def _first_author(r) -> str:
    from utils import split_facets
    f = split_facets(r.get("author"))
    return f[0].split(",")[0].strip() if f else ""


def facet_counts(series: pd.Series, unknown_label: str | None = None,
                 kind: str | None = None) -> pd.Series:
    """Value counts over ATOMIC facets of a ';'-joined multi-valued column
    ("Tragedy; History" counts once for Tragedy AND once for History)."""
    from collections import Counter
    from utils import split_facets
    c: Counter = Counter()
    n_unknown = 0
    for v in series:
        f = split_facets(v, kind=kind)
        if not f:
            n_unknown += 1
        c.update(f)
    out = pd.Series(c).sort_values(ascending=False)
    if unknown_label and n_unknown:
        out[unknown_label] = n_unknown
        out = out.sort_values(ascending=False)
    return out


def render_cluster_page(cluster_id: int, df: pd.DataFrame, labels: pd.DataFrame,
                        meta: dict, ctx: dict, summary: dict) -> str:
    # Chronological order: the genealogical reading — earliest members first,
    # successors after suit.
    sub = (df[df.cluster == cluster_id].copy()
           .sort_values(["year", "n_words"], ascending=[True, False], na_position="last")
           .reset_index(drop=True))
    n = len(sub)
    label = cluster_label_for(cluster_id, df)
    meta_entry = meta.get(cluster_id, {})
    top_words_str = labels.loc[cluster_id, "top_words"] if cluster_id in labels.index else ""
    # Excerpt extraction always uses the algorithmic c-TF-IDF words (they are
    # what the highlighting explains); curated display_keywords only change
    # what the lede SHOWS (item 1.6c).
    keywords = _parse_top_words(top_words_str)
    if "centroid_sim" not in sub.columns:
        sub["centroid_sim"] = float("nan")

    author_counts = facet_counts(sub["author"], unknown_label="(unknown)", kind="author")
    decade_counts = sub["Date_Decade"].fillna("Unknown").astype(str).value_counts().to_dict()
    genre_counts = facet_counts(sub["genre"])
    years = sub["year"].dropna()
    yr_str = f"{int(years.min())}–{int(years.max())} (median {int(years.median())})" if len(years) else "undated"

    title = f"Cluster {cluster_id} — {label.split(': ', 1)[-1]}"

    # ---- Landmarks: most typical + most familiar ----------------------
    typical = sub.nlargest(min(6, n), "centroid_sim")
    fam_mask = sub["author"].astype(str).apply(
        lambda a: any(f in a for f in FAMILIAR_AUTHORS))
    familiar = (sub[fam_mask & ~sub.index.isin(typical.index)]
                .nlargest(4, "n_words"))

    def lm_card(r, tag):
        slug = slugify(r.get("character_id", ""))
        sim = "" if pd.isna(r.get("centroid_sim")) else f" · typicality {r['centroid_sim']:.2f}"
        yr = "" if pd.isna(r.get("year")) else f", {int(r['year'])}"
        return (f'<div class="lm-card"><div class="who">'
                f'<a href="characters/{slug}.html">{esc(r.get("display_name") or "?")}</a>'
                f'<span class="badge">{tag}</span></div>'
                f'<div class="whence">{esc(truncate(str(r.get("title") or ""), 60))}'
                f'{yr} · {esc(_first_author(r))}{sim}</div></div>')

    landmarks_html = "".join([lm_card(r, "typical") for _, r in typical.iterrows()] +
                             [lm_card(r, "familiar") for _, r in familiar.iterrows()])

    # ---- Full chronological roster ------------------------------------
    dated_pos = sub.index[sub["year"].notna()].tolist()
    early_set = set(dated_pos[:5])
    table_rows = []
    for i, r in sub.iterrows():
        slug = slugify(r.get("character_id", ""))
        nm = esc(r.get("display_name") or "?")
        early = '<span class="badge">early</span>' if i in early_set else ""
        play = esc(truncate(str(r.get("title") or ""), 60))
        au = esc(_first_author(r))
        yr = "" if pd.isna(r.get("year")) else int(r["year"])
        gn = esc(r.get("genre", ""))
        nw = "" if pd.isna(r.get("n_words")) else int(r["n_words"])
        sim = "" if pd.isna(r.get("centroid_sim")) else f"{r['centroid_sim']:.2f}"
        table_rows.append(
            f"<tr><td><a href='characters/{slug}.html'>{nm}</a>{early}</td>"
            f"<td>{play}</td><td>{au}</td><td class='num' data-v='{yr if yr != '' else 9999}'>{yr}</td>"
            f"<td>{gn}</td><td class='num'>{nw}</td>"
            f"<td class='num' data-v='{sim if sim else -1}'>{sim}</td></tr>"
        )
    table_html = (
        "<table class='sortable'><thead><tr>"
        "<th>Character</th><th>Play</th><th>Author</th><th>Year</th>"
        "<th>Genre</th><th>Words</th><th>Typicality</th>"
        "</tr></thead><tbody>"
        + "".join(table_rows) + "</tbody></table>"
    )

    # ---- Representative excerpts: typical ∪ earliest ∪ familiar --------
    rep_ids = list(dict.fromkeys(          # preserve order, drop dupes
        list(typical.index) + dated_pos[:5] + list(familiar.index)))[:12]
    # why-chips: which landmark set(s) put each member here (item 1.6a)
    rep_why: dict[int, list[str]] = {}
    for i in typical.index:
        rep_why.setdefault(i, []).append("typical")
    for i in dated_pos[:5]:
        rep_why.setdefault(i, []).append("early")
    for i in familiar.index:
        rep_why.setdefault(i, []).append("familiar")
    rep = sub.loc[rep_ids].sort_values("year", na_position="last")
    excerpt_blocks = "\n".join(
        render_character_block_for_cluster_page(r, keywords, rep_why.get(i, []))
        for i, r in rep.iterrows()
    )

    # ---- Plot summaries (collapsed) ------------------------------------
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

    gtop = " · ".join(f"{esc(k)} {v / n:.0%}" for k, v in genre_counts.head(3).items())

    # ---- Tier-1 sections (2026-07-10): banner, vocabulary lede, curated
    # block, historical profile, signatures --------------------------------
    banner = render_reading_banner(summary)
    name_badge = render_name_badge(meta_entry)
    curated_block = render_curated_block(meta_entry)

    disp_kw = meta_entry.get("display_keywords") or ""
    if isinstance(disp_kw, list):
        disp_kw = ", ".join(disp_kw)
    if disp_kw.strip():
        vocab_lede = (f'<p class="lede">Register keywords (curated): <em>{esc(disp_kw)}</em></p>')
        algo_vocab_details = (f"<h3>Algorithmic distinguishing vocabulary (c-TF-IDF)</h3>"
                              f"<p><em>{esc(top_words_str)}</em> — these drive the excerpt "
                              f"highlighting below.</p>")
        kw_caveat = ""
    else:
        vocab_lede = f'<p class="lede">Distinguishing vocabulary: <em>{esc(top_words_str)}</em></p>'
        algo_vocab_details = ""
        kw_caveat = ('<p class="kw-caveat">Tokens that look like proper names in this list '
                     '(e.g. <code>massinissa</code>, <code>faukenbridge</code>) are residue of '
                     'incomplete name-masking, not register — a second masking pass is pending '
                     '(PROVENANCE_LOG §7.3).</p>')

    temporal_html, time_badges = render_temporal_strip(sub, ctx)
    time_badge_html = "".join(f'<span class="badge">{esc(b)}</span>' for b in time_badges)
    signature_html = render_signature_panel(sub, ctx)

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

<h1>{esc(title)}{name_badge}</h1>
{vocab_lede}
{kw_caveat}
{banner}

<div class="kvp">
  <span><b>{n}</b> characters</span>
  <span><b>{sub['TCP'].nunique()}</b> plays</span>
  <span><b>{len(author_counts)}</b> authors</span>
  <span>dates <b>{yr_str}</b></span>
  <span>{gtop}</span>
</div>

{curated_block}

<h2>Historical profile {time_badge_html}</h2>
{temporal_html}

<h2>Signatures</h2>
{signature_html}

<h2>Landmarks</h2>
<p class="lede" style="font-size:.92rem">The most <b>typical</b> members (closest to the
cluster centroid) and the most <b>familiar</b> ones (major-author roles). Typicality is
cosine similarity to the cluster centre — low values mean a blended, atypical member.</p>
<div class="landmarks">{landmarks_html}</div>

<h2>All {n} characters, oldest first</h2>
<p class="lede" style="font-size:.92rem">A genealogical reading: the earliest members
(<span class="badge">early</span>) are the candidate prototypes of this voice; later
members follow suit. Click a column header to re-sort.</p>
{table_html}

<h2>Representative speech excerpts</h2>
<p class="lede" style="font-size:.92rem">Shown for the typical, earliest, and familiar
members above — passages containing the cluster's distinguishing words (highlighted).</p>
{excerpt_blocks}

<details><summary>Full authorship list &amp; decade counts</summary>
<h3>Authorship (raw counts)</h3>
{render_author_tags(author_counts)}
<h3>Decade distribution (raw counts)</h3>
{render_decade_bars(decade_counts)}
{algo_vocab_details}
</details>

<details><summary>Plot summaries for the {sub['TCP'].nunique()} plays represented</summary>
{plot_html}
</details>

<div class="footer">
  Generated automatically from <code>cluster_xy_table__{config.CLUSTER_TABLES[0]}.csv</code> by
  <code>code/07_generate_site.py</code>. View the
  <a href="https://github.com/hkim1596/early-modern-drama-character-clustering">source on GitHub</a>.
</div>
</div>{SORT_JS}</body></html>"""


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
        ("Typicality",      "" if pd.isna(row.get("centroid_sim"))
                            else f"{row['centroid_sim']:.2f} (cosine to cluster centroid)"),
        ("TCP id",          row.get("TCP", "")),
        ("BritDrama no.",   "" if pd.isna(row.get("brit_drama_number")) else row.get("brit_drama_number")),
        ("Cluster",         f"Cluster {cluster_id} — {label}" if cluster_id != -1 else "Outlier (no cluster)"),
    ]:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            continue
        sval = str(val).strip()
        if not sval or sval.lower() == "nan":
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
  Generated automatically from <code>cluster_xy_table__{config.CLUSTER_TABLES[0]}.csv</code>.
  View other characters in this group on the
  {cluster_link} page.
</div>
</div></body></html>"""


def render_master_index(df: pd.DataFrame, labels: pd.DataFrame,
                        ctx: dict, summary: dict) -> str:
    meta = load_cluster_meta()
    top = load_cluster_meta_top()
    family_desc = top.get("families", {}) if isinstance(top.get("families"), dict) else {}
    family_order = list(dict.fromkeys(
        [meta[c].get("family", "Other") for c in sorted(meta)] + ["Other"]))
    by_family: dict[str, list[str]] = {f: [] for f in family_order}
    any_proposed = False

    for cid in sorted(c for c in df.cluster.unique() if c != -1):
        sub = df[df.cluster == cid]
        n = len(sub)
        top_words = labels.loc[cid, "top_words"] if cid in labels.index else ""
        entry = meta.get(cid, {})
        name = entry.get("name", "")
        headline = f"Cluster {cid} — {esc(name)}" if name \
            else f"Cluster {cid} — {esc(cluster_label_for(cid, df))}"
        prop_mark = ""
        if "proposed" in entry:
            any_proposed = True
            prop_mark = (f'<span class="prop-mark" title="{esc(entry["proposed"])}">'
                         f'proposed</span>')
        years = sub["year"].dropna()
        yr_str = f"{int(years.min())}–{int(years.max())}" if len(years) else ""
        med_str = f" · median {int(years.median())}" if len(years) else ""
        spark = render_decade_spark(sub)

        # Three exemplar members: familiar-author roles first, then most typical
        s = sub.copy()
        s["_fam"] = s["author"].astype(str).apply(
            lambda a: any(f in a for f in FAMILIAR_AUTHORS))
        s = s.sort_values(["_fam", "centroid_sim"], ascending=[False, False]) \
            if "centroid_sim" in s.columns else s
        ex = []
        for _, r in s.head(3).iterrows():
            yr = "" if pd.isna(r.get("year")) else f" {int(r['year'])}"
            ex.append(f"{esc(r.get('display_name') or '?')} "
                      f"<span style='color:var(--muted)'>({esc(truncate(str(r.get('title') or ''), 34))},{yr})</span>")
        card = f"""
<a class="idx-card" href="cluster_{cid:02d}.html">
  <h3>{headline}{prop_mark}</h3>
  <p>{' · '.join(ex)}<br>
     {n} characters · {sub['TCP'].nunique()} plays · {yr_str}{med_str}{spark}<br>
     <small>{esc(top_words)}</small></p>
</a>"""
        fam = entry.get("family", "Other")
        by_family.setdefault(fam, []).append(card)

    sections = []
    for fam in family_order:
        if by_family.get(fam):
            desc = family_desc.get(fam, "")
            desc_html = f"<p class='fam-desc'>{esc(desc)}</p>" if desc else ""
            sections.append(f"<h2 class='fam'>{esc(fam)}</h2>" + desc_html
                            + "".join(by_family[fam]))

    # Historical type coverage (item 1.5): only rendered once curated —
    # top-level "attested_types" list vs per-cluster "historical_types".
    coverage_html = ""
    attested = top.get("attested_types") or []
    if attested:
        mapped: dict[str, list[int]] = {}
        for cid, entry in meta.items():
            for t in entry.get("historical_types") or []:
                mapped.setdefault(t.lower(), []).append(cid)
        rows = []
        misses = []
        for t in attested:
            cids = sorted(mapped.get(str(t).lower(), []))
            if cids:
                links = ", ".join(f'<a href="cluster_{c:02d}.html">cl{c}</a>' for c in cids)
                rows.append(f"<tr><td>{esc(t)}</td><td>{links}</td></tr>")
            else:
                misses.append(esc(str(t)))
        miss_html = (f"<p class='lede' style='font-size:.9rem'>Attested types with <b>no "
                     f"corresponding cluster</b> (the misses are evidence too): "
                     f"{', '.join(misses)}.</p>") if misses else ""
        coverage_html = (f"<h2 class='fam'>Historical type coverage</h2>"
                         f"<table><thead><tr><th>Attested type</th><th>Cluster(s)</th></tr>"
                         f"</thead><tbody>{''.join(rows)}</tbody></table>{miss_html}")

    banner = render_reading_banner(summary)
    prop_legend = ""
    if any_proposed:
        prop_legend = ('<p class="lede" style="font-size:.9rem">Names marked '
                       '<span class="prop-mark">proposed</span> were assistant-proposed from '
                       'recorded evidence (PROVENANCE_LOG Entry 004) and await curation; '
                       'hover a marker for the evidence.</p>')

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>All clusters · Character Clustering</title>
<style>{CSS}</style>
</head><body><div class="wrap">

<nav class="crumbs"><a href="index.html">Home</a> › <span>All clusters</span></nav>
<h1>Character archetypes — all clusters</h1>
<p class="lede">{df.cluster.nunique() - 1} voice clusters over {(df.cluster >= 0).sum():,}
characters from {df.loc[df.cluster >= 0, "TCP"].nunique()} plays, grouped into families.
Each cluster page lists every member chronologically (candidate prototypes first), with
landmarks, typicality scores, and speech evidence. Characters speaking fewer than 150
words are not clustered, and only one edition of each play is included.</p>
{banner}
{prop_legend}
{''.join(sections)}

{coverage_html}

<div class="footer">
  Generated automatically by <code>code/07_generate_site.py</code>.
</div>
</div></body></html>"""


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Generate the static evidence site")
    ap.add_argument("--no-characters", action="store_true",
                    help="regenerate cluster pages + master index only; leave the "
                         "existing docs/characters/ pages untouched (they do not "
                         "depend on the cluster-page template)")
    args = ap.parse_args()

    cxy = config.DATA_DIR / f"cluster_xy_table__{config.CLUSTER_TABLES[0]}.csv"
    if not cxy.exists():
        raise FileNotFoundError(f"{cxy} not found. Run 04_cluster.py first.")
    df = pd.read_csv(cxy, low_memory=False)
    # Analysis-grade year (performance year, pre-fill) captured BEFORE
    # derive_display_columns applies the Entry-005 display fills — the
    # historical-profile strip and its badges use this; see _analysis_years.
    _yr = pd.to_numeric(df["year"], errors="coerce")
    _need = _yr.isna() & df["year"].notna()
    _yr.loc[_need] = pd.to_numeric(
        df.loc[_need, "year"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
    from utils import derive_display_columns
    df = derive_display_columns(
        df, fills_path=config.DATA_DIR / "manual_metadata_fills.json")
    df["year_analysis"] = _yr
    df["cluster"] = df["cluster"].astype(int)

    lbl_path = config.DATA_DIR / f"cluster_labels__{config.CLUSTER_TABLES[0]}.csv"
    if lbl_path.exists():
        labels = pd.read_csv(lbl_path).set_index("cluster")
    else:
        labels = pd.DataFrame(columns=["top_words"]).set_index(pd.Index([], name="cluster"))

    meta = load_cluster_meta()
    summary = load_cluster_summary()
    ctx = corpus_context(df)
    print(f"📊 Corpus baselines (clustered, dated n={ctx['dated_n']}): "
          f"median {ctx['median']}, pre-1590 {ctx['pre_share']:.1%}, "
          f"post-1625 {ctx['post_share']:.1%}")

    out_dir = config.RESULTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    chars_dir = out_dir / "characters"
    chars_dir.mkdir(parents=True, exist_ok=True)

    # 1) cluster pages (non-outlier clusters only)
    clusters = sorted(c for c in df.cluster.unique() if c != -1)
    for cid in clusters:
        (out_dir / f"cluster_{cid:02d}.html").write_text(
            render_cluster_page(cid, df, labels, meta, ctx, summary), encoding="utf-8"
        )
    print(f"✅ {len(clusters)} cluster pages written")

    # 2) master cluster index
    (out_dir / "cluster_evidence.html").write_text(
        render_master_index(df, labels, ctx, summary), encoding="utf-8"
    )
    print(f"✅ cluster_evidence.html written")

    # 3) character pages (only for characters in non-outlier clusters)
    if args.no_characters:
        print("⏭  character pages skipped (--no-characters)")
    else:
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
