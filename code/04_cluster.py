"""Stage 04 — Archetype clustering: LOO play centering → spherical k-means.

This REPLACES the original UMAP→HDBSCAN preset pipeline (see git history).
Rationale (diagnosed 2026-07-06 on the first full run):
  1. Document LENGTH dominated the raw embedding space (log word count
     recoverable from top-5 PCs with R²=0.90), so HDBSCAN either shattered
     (70.8% outliers) or blobbed (one 8.2k cluster). Real fix = chunked
     re-embedding (stage 03, EMBED_CHUNK_TOKENS); interim fix = linear
     length-axis deflation here (LENGTH_DEFLATE_ROUNDS).
  2. What wasn't length was play/genre/topic. Leave-one-out play centering
     (subtract the centroid of the character's play-mates) converts "what the
     play is about" into "how this character differs from co-characters" —
     which is what an archetype is.
  3. Archetypes are a continuum, not density islands: every character should
     get a type, so partitional k-means (cosine/spherical) fits the goal;
     HDBSCAN's noise concept does not.

Pipeline:
  load → L2-normalize → LOO play centering (full corpus) → optional length
  deflation (full corpus) → filter to n_words ≥ MIN_WORDS_CLUSTER →
  re-normalize → k-means (+ silhouette k-sweep diagnostics) → profiles +
  master table for stages 05–07.

Inputs (DATA_DIR):   character_documents.csv, embeddings.npy
Outputs (DATA_DIR), suffixed by --name (default "archetype"):
  - cluster_xy_table__<name>.csv    master table = documents + x/y + cluster +
                                    centroid_sim; consumed by stages 05–07.
                                    cluster = -1 marks characters below the
                                    word threshold (not clustered).
  - cluster_profiles__<name>.md     sizes, genres, top names, exemplars
  - cluster_k_sweep__<name>.csv     silhouette diagnostics over KMEANS_K_SWEEP
  - cluster_summary__<name>.json    parameters + length-R² audit trail

Usage:
  python code/04_cluster.py                 # defaults from config
  python code/04_cluster.py --k 30          # try another k
  python code/04_cluster.py --no-sweep      # skip k diagnostics
  python code/04_cluster.py --agglo         # + agglomerative cross-check
  python code/04_cluster.py --name archetype_wholedoc   # e.g. control run
"""

from __future__ import annotations
import argparse
import json

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

import config


# ----------------------------------------------------------------------
# Representation
# ----------------------------------------------------------------------
def l2(M: np.ndarray) -> np.ndarray:
    return M / np.clip(np.linalg.norm(M, axis=1, keepdims=True), 1e-12, None)


def loo_play_centering(embn: np.ndarray, plays: np.ndarray) -> np.ndarray:
    """Subtract, from each character, the mean embedding of the OTHER
    characters in the same play (leave-one-out, so a character is never
    centered against itself). Single-character plays are left unchanged."""
    cent = np.empty_like(embn)
    n_single = 0
    for p in pd.unique(plays):
        idx = np.where(plays == p)[0]
        if len(idx) == 1:
            cent[idx] = embn[idx]
            n_single += 1
            continue
        s = embn[idx].sum(0)
        loo = (s[None, :] - embn[idx]) / (len(idx) - 1)
        cent[idx] = embn[idx] - loo
    if n_single:
        print(f"   ℹ️  {n_single} single-character play(s) left uncentered")
    return l2(cent)


def deflate_length(X: np.ndarray, logw: np.ndarray, rounds: int) -> np.ndarray:
    """Iteratively remove the ridge-regression direction that best predicts
    log word count. Linear-only: with legacy whole-doc embeddings some
    nonlinear length signal survives — chunked re-embedding is the real fix."""
    X = X.copy()
    y = (logw - logw.mean()).astype(np.float32)
    for _ in range(rounds):
        Xc = X - X.mean(0)
        w = np.linalg.lstsq(
            Xc.T @ Xc + 10.0 * np.eye(X.shape[1], dtype=np.float32),
            Xc.T @ y, rcond=None)[0]
        w /= np.linalg.norm(w)
        X = X - np.outer(X @ w, w)
    return l2(X)


def length_r2(M: np.ndarray, logw: np.ndarray, n_pcs: int = 5) -> float:
    """R² of log(word count) from the top principal components — the audit
    metric for the length confound (raw legacy embeddings: 0.90)."""
    Z = M - M.mean(0)
    C = (Z.T @ Z) / len(Z)
    _, vecs = np.linalg.eigh(C)
    P = Z @ vecs[:, -n_pcs:]
    A = np.column_stack([P, np.ones(len(P))])
    coef, *_ = np.linalg.lstsq(A, logw, rcond=None)
    resid = logw - A @ coef
    return float(1 - (resid**2).sum() / ((logw - logw.mean())**2).sum())


# ----------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------
def cluster_profiles(sub: pd.DataFrame, X: np.ndarray, centers: np.ndarray) -> str:
    genre = sub["genre_brit_display"].fillna(sub["genre_annals_display"])
    lines = ["# Archetype cluster profiles", ""]
    for cl, g in sorted(sub.groupby("cluster"), key=lambda kv: -len(kv[1])):
        gen = genre.loc[g.index].value_counts()
        names = g["normalized_name"].astype(str).str.lower().value_counts()
        plays = g["TCP"].value_counts()
        idx = g.index.to_numpy()
        sims = X[idx] @ centers[cl]
        ex = g.loc[idx[np.argsort(-sims)][:8]]

        def src(r):
            t = r.title if pd.notna(r.title) else r.TCP
            try:
                y = int(float(r.year))
            except (TypeError, ValueError):
                y = str(r.year).strip("[]") if pd.notna(r.year) else "?"
            return f"{r.display_name} ({str(t)[:40]}, {y})"
        exemplars = "; ".join(src(r) for r in ex.itertuples())
        gtop = ", ".join(f"{k} {v/len(g):.0%}" for k, v in gen.head(3).items())
        lines += [
            f"## Cluster {cl}  (n={len(g)})",
            "",
            f"- median words: {int(g.n_words.median())} | plays: {g.TCP.nunique()} "
            f"| top-play share: {plays.iloc[0]/len(g):.1%}",
            f"- genres: {gtop}",
            f"- top names: {', '.join(names.head(12).index)}",
            f"- exemplars (nearest centroid): {exemplars}",
            "",
        ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--k", type=int, default=config.KMEANS_K)
    ap.add_argument("--min-words", type=int, default=config.MIN_WORDS_CLUSTER)
    ap.add_argument("--deflate", type=int, default=config.LENGTH_DEFLATE_ROUNDS)
    ap.add_argument("--name", default=config.CLUSTER_TABLES[0],
                    help="output suffix, e.g. a control run on other embeddings")
    ap.add_argument("--no-sweep", action="store_true", help="skip silhouette k-sweep")
    ap.add_argument("--sweep-sample", type=int, default=3000,
                    help="silhouette sample size during the k-sweep")
    ap.add_argument("--agglo", action="store_true",
                    help="also fit average-linkage agglomerative at k and report ARI "
                         "(needs ~n² memory)")
    ap.add_argument("--no-umap", action="store_true", help="skip 2-D UMAP (x/y stay empty)")
    args = ap.parse_args()

    df = pd.read_csv(config.DATA_DIR / "character_documents.csv", low_memory=False)
    emb = np.load(config.DATA_DIR / "embeddings.npy").astype(np.float32)
    assert len(df) == emb.shape[0], \
        f"Row mismatch: documents={len(df)}, embeddings={emb.shape[0]}"
    print(f"📄 Documents: {len(df)}   Embeddings: {emb.shape}")

    logw = np.log10(df["n_words"].clip(lower=1)).values
    embn = l2(emb)
    r2_raw = length_r2(embn, logw)
    print(f"📏 length R² (raw):      {r2_raw:.3f}")

    print("🎭 Leave-one-out play centering")
    X = loo_play_centering(embn, df["TCP"].values)
    r2_centered = length_r2(X, logw)
    print(f"📏 length R² (centered): {r2_centered:.3f}")

    r2_deflated = None
    if args.deflate > 0:
        print(f"📐 Length-axis deflation × {args.deflate}")
        X = deflate_length(X, logw, args.deflate)
        r2_deflated = length_r2(X, logw)
        print(f"📏 length R² (deflated): {r2_deflated:.3f}")

    mask = df["n_words"].values >= args.min_words
    n_dup = 0
    if getattr(config, "DEDUPE_EDITIONS", False):
        from utils import canonical_edition_tcps
        # Canonical-edition overrides (e.g. New Oxford Shakespeare choices)
        prefer, year_fill = set(), {}
        can_path = config.DATA_DIR / "canonical_editions.json"
        if can_path.exists():
            with open(can_path, encoding="utf-8") as f:
                for w in json.load(f).get("works", {}).values():
                    prefer.add(w["keep"])
                    if w.get("year"):
                        year_fill[w["keep"]] = w["year"]
            print(f"📖 Canonical-edition overrides: {len(prefer)} "
                  f"(data/canonical_editions.json)")

        keep_tcps, report = canonical_edition_tcps(df, prefer=prefer)
        dup = ~df["TCP"].isin(keep_tcps).values
        n_dup = int((dup & mask).sum())
        mask = mask & ~dup
        print(f"📚 Edition dedup: {len(report)} multi-edition works — "
              f"{n_dup} duplicate-edition characters excluded from clustering "
              f"(kept in the table and embeddings; excluded here only)")

        # Full inclusion/exclusion record — one row per edition in every
        # multi-edition group.
        rec_rows = []
        for r in report:
            for m in r["members"]:
                rec_rows.append({
                    "work": r["work"], "TCP": m["TCP"], "title": m["title"],
                    "year": m["year"], "total_words": m["total_words"],
                    "n_characters": m["n_characters"],
                    "included_in_clustering": m["included"],
                    "selection_policy": r["policy"] if m["included"] else "",
                    "kept_edition": r["kept"],
                })
        rec_path = config.DATA_DIR / f"edition_dedup__{args.name}.csv"
        pd.DataFrame(rec_rows).to_csv(rec_path, index=False)
        print(f"   ↳ {rec_path.name} ({len(rec_rows)} edition rows)")

        # Working dates for undated canonical texts (e.g. Folio-only items):
        # first-performance year from canonical_editions.json, so chronology
        # on the site stays meaningful.
        for tcp, yr in year_fill.items():
            if tcp in keep_tcps:
                sel = (df["TCP"] == tcp) & df["year"].isna()
                if sel.any():
                    df.loc[sel, "year"] = str(yr)   # year column is str-typed
    sub = df.loc[mask, ["TCP", "display_name", "normalized_name", "title", "year",
                        "n_words", "genre_brit_display", "genre_annals_display"]
                 ].reset_index(drop=True)
    Xf = l2(X[mask])
    kept_words = df.loc[mask, "n_words"].sum() / df["n_words"].sum()
    print(f"🔎 Filter ≥{args.min_words} words: kept {mask.sum()}/{len(df)} characters "
          f"({kept_words:.1%} of corpus words); dropped characters get cluster = -1")

    # ---- k-sweep diagnostics -----------------------------------------
    if not args.no_sweep:
        print(f"🧪 k-sweep {config.KMEANS_K_SWEEP} "
              f"(silhouette, cosine, sample={args.sweep_sample})")
        rows = []
        for k in config.KMEANS_K_SWEEP:
            km = KMeans(n_clusters=k, n_init=4, random_state=config.RANDOM_STATE)
            lab = km.fit_predict(Xf)
            sil = silhouette_score(Xf, lab, metric="cosine",
                                   sample_size=min(args.sweep_sample, len(Xf)),
                                   random_state=config.RANDOM_STATE)
            sizes = np.bincount(lab)
            rows.append({"k": k, "silhouette_cos": round(float(sil), 4),
                         "min_size": int(sizes.min()), "max_size": int(sizes.max())})
            print(f"   k={k:>3}  silhouette={sil:.4f}  "
                  f"sizes {sizes.min()}–{sizes.max()}")
        pd.DataFrame(rows).to_csv(
            config.DATA_DIR / f"cluster_k_sweep__{args.name}.csv", index=False)
        print(f"   ↳ cluster_k_sweep__{args.name}.csv (pick k by silhouette AND "
              "profile interpretability — silhouette alone favors degenerate small k)")

    # ---- final model --------------------------------------------------
    print(f"🚀 Final spherical k-means: k={args.k}")
    km = KMeans(n_clusters=args.k, n_init=10, random_state=config.RANDOM_STATE)
    raw_lab = km.fit_predict(Xf)
    # relabel so cluster 0 is the largest
    order = np.argsort(-np.bincount(raw_lab))
    remap = np.empty_like(order); remap[order] = np.arange(args.k)
    lab = remap[raw_lab]
    centers = l2(km.cluster_centers_)[order]

    sil_full = silhouette_score(Xf, lab, metric="cosine")
    print(f"   silhouette (cosine, full): {sil_full:.4f}")

    ari = None
    if args.agglo:
        from sklearn.cluster import AgglomerativeClustering
        from sklearn.metrics import adjusted_rand_score
        print("🌳 Agglomerative (average linkage, cosine) comparison")
        ag = AgglomerativeClustering(n_clusters=args.k, metric="cosine",
                                     linkage="average").fit_predict(Xf)
        ari = float(adjusted_rand_score(lab, ag))
        print(f"   ARI k-means vs agglomerative: {ari:.3f}")

    sub["cluster"] = lab

    xy = None
    if not args.no_umap:
        try:
            from umap import UMAP
            print("🗺  UMAP → 2D (for plotting only)")
            xy = UMAP(n_components=2, n_neighbors=30, min_dist=0.1, metric="cosine",
                      random_state=config.RANDOM_STATE).fit_transform(Xf)
        except ImportError:
            print("   ⚠️ umap-learn not installed — x/y left empty")

    # ---- master table for stages 05–07 --------------------------------
    out_df = df.copy()
    out_df["cluster"] = -1
    out_df.loc[mask, "cluster"] = lab
    out_df["centroid_sim"] = np.nan
    out_df.loc[mask, "centroid_sim"] = (Xf * centers[lab]).sum(1).round(4)
    out_df["x"] = np.nan
    out_df["y"] = np.nan
    if xy is not None:
        out_df.loc[mask, "x"] = xy[:, 0].round(4)
        out_df.loc[mask, "y"] = xy[:, 1].round(4)
    table_path = config.DATA_DIR / f"cluster_xy_table__{args.name}.csv"
    out_df.to_csv(table_path, index=False)

    (config.DATA_DIR / f"cluster_profiles__{args.name}.md").write_text(
        cluster_profiles(sub, Xf, centers), encoding="utf-8")

    summary = {
        "name": args.name,
        "k": args.k,
        "min_words": args.min_words,
        "deflate_rounds": args.deflate,
        "n_clustered": int(mask.sum()),
        "n_below_threshold": int((~mask).sum()),
        "n_duplicate_editions_excluded": n_dup,
        "corpus_words_kept": round(float(kept_words), 4),
        "silhouette_cosine_full": round(float(sil_full), 4),
        "ari_vs_agglomerative": ari,
        "length_r2_raw": round(float(r2_raw), 4),
        "length_r2_centered": round(float(r2_centered), 4),
        "length_r2_final": round(float(r2_deflated if r2_deflated is not None
                                       else r2_centered), 4),
        "embedding_rows": int(emb.shape[0]),
        "random_state": config.RANDOM_STATE,
    }
    with open(config.DATA_DIR / f"cluster_summary__{args.name}.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ {table_path.name}, cluster_profiles__{args.name}.md, "
          f"cluster_summary__{args.name}.json written")
    print("   Next: 05_label_clusters.py → 06_visualize.py → 07_generate_site.py. "
          "If profiles look length-stratified, re-embed with EMBED_CHUNK_TOKENS "
          "and set LENGTH_DEFLATE_ROUNDS=0.")


if __name__ == "__main__":
    main()
