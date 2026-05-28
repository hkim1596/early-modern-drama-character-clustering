"""Stage 04 — UMAP-5D → HDBSCAN → UMAP-2D, run for every preset in config.PRESETS.

Inputs (in DATA_DIR):
  - character_documents.csv
  - embeddings.npy

Outputs (per preset, in DATA_DIR):
  - reduced_5d__<preset>.npy
  - clusters_hdbscan__<preset>.npy
  - reduced_2d__<preset>.npy
  - cluster_xy_table__<preset>.csv     master table = documents + x + y + cluster
And:
  - preset_summary.csv
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from umap import UMAP
from hdbscan import HDBSCAN

import config


def run_preset(df: pd.DataFrame, embeddings: np.ndarray, preset: dict) -> dict:
    name = preset["name"]
    print(f"\n{'=' * 70}")
    print(f"🚀 Preset: {name}")
    print("=" * 70)

    print("🧩 UMAP → 5D")
    red_5d = UMAP(**preset["umap_5d"]).fit_transform(embeddings)
    np.save(config.DATA_DIR / f"reduced_5d__{name}.npy", red_5d)

    print("🧪 HDBSCAN")
    hdb = HDBSCAN(**preset["hdbscan"]).fit(red_5d)
    clusters = hdb.labels_.astype(int)
    np.save(config.DATA_DIR / f"clusters_hdbscan__{name}.npy", clusters)

    n_total = len(clusters)
    n_outliers = int((clusters == -1).sum())
    unique = sorted(set(clusters.tolist()))
    n_clusters = len(unique) - (1 if -1 in unique else 0)
    pct = (n_outliers / n_total) if n_total else 0.0
    vc = pd.Series(clusters).value_counts()
    print(f"   total={n_total}  clusters={n_clusters}  outliers={n_outliers} ({pct:.1%})")
    print(f"   top sizes: {dict(vc.head(8))}")

    print("🗺  UMAP → 2D")
    red_2d = UMAP(**preset["umap_2d"]).fit_transform(embeddings)
    np.save(config.DATA_DIR / f"reduced_2d__{name}.npy", red_2d)

    out_df = df.copy()
    out_df["x"] = red_2d[:, 0]
    out_df["y"] = red_2d[:, 1]
    out_df["cluster"] = clusters
    out_df.to_csv(config.DATA_DIR / f"cluster_xy_table__{name}.csv", index=False)

    return {
        "preset": name,
        "n_total": n_total,
        "n_clusters_excl_-1": n_clusters,
        "n_outliers": n_outliers,
        "outliers_pct": round(pct * 100, 2),
        "largest_cluster_size": int(vc.iloc[0]) if len(vc) else 0,
    }


def main() -> None:
    df = pd.read_csv(config.DATA_DIR / "character_documents.csv")
    embeddings = np.load(config.DATA_DIR / "embeddings.npy")
    assert len(df) == embeddings.shape[0], (
        f"Row mismatch: documents={len(df)}, embeddings={embeddings.shape[0]}"
    )
    print(f"📄 Documents: {len(df)}   Embeddings: {embeddings.shape}")

    summary_rows = [run_preset(df, embeddings, p) for p in config.PRESETS]
    pd.DataFrame(summary_rows).to_csv(config.DATA_DIR / "preset_summary.csv", index=False)
    print("\n✅ preset_summary.csv written")


if __name__ == "__main__":
    main()
