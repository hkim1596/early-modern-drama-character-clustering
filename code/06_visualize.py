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

    point_colors = [color_map[l] for l in df["topic_label"]]
    n = len(df)

    fig = go.Figure()
    # Trace 0: the actual points. Restyle calls update this trace.
    fig.add_trace(go.Scattergl(
        x=df["x"], y=df["y"], mode="markers",
        marker=dict(size=5, opacity=0.7, color=point_colors,
                    line=dict(width=0, color="rgba(0,0,0,0)")),
        hovertext=df["_hover"], hoverinfo="text",
        showlegend=False,
        name="points",
    ))
    # Invisible traces just to populate the cluster legend
    for lab in labels:
        fig.add_trace(go.Scattergl(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=color_map[lab]),
            name=lab, showlegend=True,
        ))

    # ----- Dropdown highlight menus -----
    base_size    = [5] * n
    base_opacity = [0.7] * n
    base_line_w  = [0] * n
    base_line_c  = ["rgba(0,0,0,0)"] * n

    def reset_args() -> dict:
        return {
            "marker.size":      [base_size],
            "marker.opacity":   [base_opacity],
            "marker.line.width":[base_line_w],
            "marker.line.color":[base_line_c],
        }

    # Pre-build the list of (axis, label, sorted values) to know how many we have
    axes_to_show = []
    for col, label in HIGHLIGHT_AXES:
        if col not in df.columns:
            continue
        raw_values = [v for v in df[col].dropna().unique().tolist()
                      if str(v).strip() and str(v).lower() != "unknown"]
        if not raw_values:
            continue
        if col == "Date_Decade":
            values = sort_decades([str(v) for v in raw_values])
        else:
            values = sorted([str(v) for v in raw_values])
        axes_to_show.append((col, label, values))

    # Layout: dropdowns in a single horizontal row above the plot, legend on the right.
    updatemenus = []
    n_axes = len(axes_to_show)
    # Distribute dropdowns across the plot's width (x = 0.0 .. 0.92 in figure-relative coords)
    x_step = (0.92 / max(n_axes - 1, 1)) if n_axes > 1 else 0
    for i, (col, label, values) in enumerate(axes_to_show):
        buttons = [dict(label=f"All ({label})", method="restyle",
                        args=[reset_args(), [0]])]
        for v in values:
            mask = (df[col].astype(str) == v).tolist()
            buttons.append(dict(
                label=f"{label}: {v}",
                method="restyle",
                args=[{
                    "marker.size":       [[10 if m else 3   for m in mask]],
                    "marker.opacity":    [[0.95 if m else 0.20 for m in mask]],
                    "marker.line.width": [[1.5 if m else 0   for m in mask]],
                    "marker.line.color": [["black" if m else "rgba(0,0,0,0)" for m in mask]],
                }, [0]],
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
        legend=dict(title="Cluster", itemsizing="constant",
                    x=1.02, xanchor="left", y=1.0, yanchor="top"),
        updatemenus=updatemenus,
        width=1400, height=920,
        margin=dict(l=40, r=300, t=160, b=40),
    )
    return fig


def main() -> None:
    for preset in config.PRESETS:
        name = preset["name"]
        path = config.DATA_DIR / f"cluster_xy_table__{name}.csv"
        if not path.exists():
            print(f"⚠ {name}: missing {path.name} — run 04 first")
            continue
        df = pd.read_csv(path)
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
