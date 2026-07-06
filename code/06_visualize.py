"""Stage 06 — Interactive Plotly map per preset, with dropdown highlight menus.

Each point is one character. Color encodes cluster. Dropdown menus let you
highlight a single decade / genre / author / play title at a time (others fade
to background).

Inputs (in DATA_DIR):
  - cluster_xy_table__<preset>.csv  (with topic_label from stage 05)

Outputs (in RESULTS_DIR):
  - interactive_clusters__<preset>.html
"""

from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config


HIGHLIGHT_AXES = [
    ("Date_Decade", "Decade"),
    ("genre",       "Genre"),
    ("author",      "Author"),
    ("title",       "Title"),
    ("play_type",   "Play type"),
    ("theater",     "Theater"),
    ("company",     "Company"),
]


def sort_decades(values: list[str]) -> list[str]:
    known, unknown = [], []
    for v in values:
        (unknown if str(v).lower() == "unknown" else known).append(v)
    known.sort(key=lambda v: int(str(v).rstrip("s")) if str(v).rstrip("s").isdigit() else 10**9)
    return known + unknown


def label_sort_key(label: str) -> int:
    head = str(label).split(":", 1)[0].strip()
    try:
        return int(head)
    except ValueError:
        return 10**9


def build_figure(df: pd.DataFrame, preset_name: str) -> go.Figure:
    df = df.copy().reset_index(drop=True)
    df["topic_label"] = df["topic_label"].fillna("-1: outliers").astype(str)

    # Build hover text per row, skipping fields that are empty for that row.
    def col(name: str) -> pd.Series:
        s = df.get(name, pd.Series([""] * len(df)))
        return s.astype(object).where(s.notna(), "")

    char_name = col("display_name").where(col("display_name").astype(bool), col("normalized_name"))
    raw_names = col("raw_names")
    title_s   = col("title")
    author_s  = col("author")
    decade_s  = col("Date_Decade")
    year_s    = col("year").astype(str).where(col("year").astype(str) != "nan", "")
    date_perf = col("date_first_performance")
    genre_s   = col("genre")
    play_t_s  = col("play_type")
    theater_s = col("theater")
    company_s = col("company")
    role_s    = col("role_description")
    words_s   = col("top_words")

    hover_lines = []
    fields = [
        ("Play",            title_s),
        ("Author",          author_s),
        ("Date",            date_perf.where(date_perf.astype(bool), year_s)),
        ("Decade",          decade_s),
        ("Genre",           genre_s),
        ("Play type",       play_t_s),
        ("Theater",         theater_s),
        ("Company",         company_s),
        ("Character",       char_name),
        ("Role",            role_s),
        ("Cluster",         df["topic_label"]),
        ("Top words",       words_s),
    ]
    # Build a single hover string per row, skipping empty fields.
    def row_hover(i: int) -> str:
        parts = []
        for label, series in fields:
            v = str(series.iloc[i]).strip()
            if not v or v.lower() in ("nan", "none", "unknown"):
                continue
            parts.append(f"{label}: {v}")
        # Append raw_names as a small dim line under Character, if useful
        rn = str(raw_names.iloc[i]).strip()
        cn = str(char_name.iloc[i]).strip()
        if rn and rn != cn:
            # Insert (raw: …) right after the Character line
            for j, p in enumerate(parts):
                if p.startswith("Character:"):
                    parts.insert(j + 1, f"  (raw: {rn})")
                    break
        return "<br>".join(parts)

    df["_hover"] = [row_hover(i) for i in range(len(df))]

    # Cluster color map (qualitative; -1 grey)
    labels = sorted(df["topic_label"].unique().tolist(), key=label_sort_key)
    palette = (
        px.colors.qualitative.Plotly
        + px.colors.qualitative.Set3
        + px.colors.qualitative.Dark24
    )
    color_map = {lab: palette[i % len(palette)] for i, lab in enumerate(labels)}
    color_map["-1: outliers"] = "lightgrey"

    # ----- One trace per cluster -----
    # Native legend interactivity: click a legend entry to hide that cluster,
    # double-click to isolate it. (The old design had a single points trace
    # plus dummy legend entries, so legend clicks did nothing.)
    fig = go.Figure()
    trace_rows: list[list[int]] = []   # df row positions per trace
    pos_in_trace = {}                  # df row position -> (trace_i, index within trace)
    for t_i, lab in enumerate(labels):
        rows = df.index[df["topic_label"] == lab].tolist()
        trace_rows.append(rows)
        for j, r in enumerate(rows):
            pos_in_trace[r] = (t_i, j)
        fig.add_trace(go.Scattergl(
            x=df.loc[rows, "x"], y=df.loc[rows, "y"], mode="markers",
            marker=dict(size=5, opacity=0.75, color=color_map[lab]),
            selected=dict(marker=dict(size=9, opacity=1.0)),
            unselected=dict(marker=dict(size=4, opacity=0.12)),
            hovertext=df.loc[rows, "_hover"], hoverinfo="text",
            name=lab, showlegend=True,
        ))
    n_traces = len(labels)
    all_trace_idx = list(range(n_traces))

    # ----- Dropdown highlight menus -----
    # Selecting a value sets `selectedpoints` per trace: members render at
    # full size/opacity, everything else dims (unselected style). Payload per
    # option is just the member indices, so the HTML stays small (per-option
    # full-length restyle arrays once made this file >100 MB).
    #
    # Metadata fields are multi-valued (";"-joined: "Adult Professional;
    # Professional", "Fletcher, John; Massinger, Philip"), so options are
    # built from ATOMIC facets: a point matches "Adult Professional" whether
    # or not other types are listed alongside it.
    from utils import split_facets
    axes_to_show = []
    for col, label in HIGHLIGHT_AXES:
        if col not in df.columns:
            continue
        facet_rows: dict[str, list[int]] = {}
        kind = "author" if col == "author" else None
        for r, v in df[col].items():
            for f in split_facets(v, kind=kind):
                facet_rows.setdefault(f, []).append(r)
        if not facet_rows:
            continue
        if col == "Date_Decade":
            values = sort_decades(list(facet_rows))
        else:
            values = sorted(facet_rows)
        axes_to_show.append((col, label, values, facet_rows))

    reset_sel = {"selectedpoints": [None] * n_traces}

    updatemenus = []
    n_axes = len(axes_to_show)
    x_step = (0.92 / max(n_axes - 1, 1)) if n_axes > 1 else 0
    for i, (col, label, values, facet_rows) in enumerate(axes_to_show):
        buttons = [dict(label=f"All ({label})", method="restyle",
                        args=[reset_sel, all_trace_idx])]
        for v in values:
            rows = facet_rows[v]
            per_trace: list[list[int]] = [[] for _ in range(n_traces)]
            for r in rows:
                t_i, j = pos_in_trace[r]
                per_trace[t_i].append(j)
            buttons.append(dict(
                label=f"{label}: {v} ({len(rows)})",
                method="restyle",
                args=[{"selectedpoints": per_trace}, all_trace_idx],
            ))

        updatemenus.append(dict(
            buttons=buttons, direction="down", showactive=True,
            x=i * x_step, xanchor="left",
            y=1.04, yanchor="bottom",
            bgcolor="white", bordercolor="lightgrey",
            pad=dict(l=0, r=0, t=0, b=0),
        ))

    fig.update_layout(
        title=dict(text=f"Character Clusters — {preset_name}",
                   x=0.5, xanchor="center",
                   y=0.98, yanchor="top",
                   font=dict(size=18)),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        legend=dict(title="Cluster<br><span style='font-size:11px;color:#888'>click: hide · double-click: isolate</span>",
                    itemsizing="constant",
                    x=1.02, xanchor="left", y=1.0, yanchor="top"),
        updatemenus=updatemenus,
        width=1400, height=920,
        margin=dict(l=40, r=300, t=160, b=40),
    )
    return fig


def main() -> None:
    for name in config.CLUSTER_TABLES:
        path = config.DATA_DIR / f"cluster_xy_table__{name}.csv"
        if not path.exists():
            print(f"⚠ {name}: missing {path.name} — run 04 first")
            continue
        df = pd.read_csv(path, low_memory=False)
        from utils import derive_display_columns
        df = derive_display_columns(df)
        # keep only the columns the figure uses — the full table (speech text
        # etc.) would otherwise be serialized into the HTML (>100 MB)
        keep = ["x", "y", "cluster", "topic_label", "display_name",
                "normalized_name", "raw_names", "title", "author", "year",
                "date_first_performance", "Date_Decade", "genre", "play_type",
                "theater", "company", "role_description", "top_words"]
        df = df[[c for c in keep if c in df.columns]]
        if "topic_label" not in df.columns:
            print(f"⚠ {name}: topic_label missing — run 05 first")
            continue
        df_plot = df[df["cluster"] != -1].copy()
        fig = build_figure(df_plot, name)
        out = config.RESULTS_DIR / f"interactive_clusters__{name}.html"
        fig.write_html(out, include_plotlyjs="cdn")
        print(f"✅ {out}")


if __name__ == "__main__":
    main()
