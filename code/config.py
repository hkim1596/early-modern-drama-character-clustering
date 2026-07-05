"""Configuration for the character-clustering pipeline.

All paths and hyperparameters live here. Override the base directory at runtime
with `CHAR_CLUSTERING_BASE=/path/to/project python 03_embed.py` (useful when
running stage 03 on a GPU server with a different filesystem layout).
"""

from __future__ import annotations
import os
from pathlib import Path

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
# Project root = parent of the `code/` directory this file lives in.
# That way the pipeline works no matter what the project folder is renamed to
# and works equivalently on Mac, the GPU server, or any other machine.
_HERE     = Path(__file__).resolve().parent
OUT_DIR   = Path(os.environ.get("CHAR_CLUSTERING_BASE", _HERE.parent))
BASE_DIR  = OUT_DIR      # back-compat alias

DATA_DIR    = OUT_DIR / "data"
RESULTS_DIR = OUT_DIR / "docs"     # GitHub Pages serves from /docs

# All raw + intermediate data lives under DATA_DIR
JSON_DIR      = DATA_DIR / "character_json_all"
META_XLSX     = DATA_DIR / "british_drama_matched_cleaned.xlsx"
DEEP_TCP_XLSX = DATA_DIR / "deep_tcp.xlsx"
METADATA_CSV  = DATA_DIR / "metadata.csv"          # produced by merge of the two above

DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------
# Embedding
# -------------------------------------------------------------------
EMBED_MODEL      = "Alibaba-NLP/gte-Qwen2-1.5B-instruct"
EMBED_MAX_TOKENS = 32768   # gte-Qwen2 native context
EMBED_BATCH_SIZE = 1       # safe default for long inputs; raise if VRAM allows
EMBED_INSTRUCTION = "Represent the unique speech style and rhetorical signature of this dramatic character for similarity comparison."

# -------------------------------------------------------------------
# Filtering
# -------------------------------------------------------------------
MIN_SPEECH_CHARS = 200   # drop characters with very short speech text

# -------------------------------------------------------------------
# Name normalization
# -------------------------------------------------------------------
NAME_MATCH_AUTO_THRESHOLD   = 92   # rapidfuzz score >= this  -> auto-merge to catalogue name
NAME_MATCH_REVIEW_THRESHOLD = 70   # 70-92  -> keep raw name (no merge), just flag for review

# Speech prefixes that are not actually characters (groups, stage directions, etc.)
GENERIC_LABELS = {
    "all", "all speak", "all speake", "all speaketh", "all together", "all three", "all four",
    "both", "omnes", "chorus", "song", "songs", "song within", "within", "epilogue", "prologue",
}

# -------------------------------------------------------------------
# Clustering presets (UMAP-5D -> HDBSCAN -> UMAP-2D)
# -------------------------------------------------------------------
RANDOM_STATE = 42

PRESETS = [
    {
        "name": "baseline",
        "umap_5d": dict(n_components=5, n_neighbors=15, min_dist=0.05,
                        metric="cosine", random_state=RANDOM_STATE),
        "hdbscan": dict(min_cluster_size=20, min_samples=None,
                        metric="euclidean", cluster_selection_method="eom"),
        "umap_2d": dict(n_components=2, n_neighbors=15, min_dist=0.0,
                        metric="cosine", random_state=RANDOM_STATE),
    },
    {
        "name": "tuned_less_outliers",
        "umap_5d": dict(n_components=5, n_neighbors=35, min_dist=0.10,
                        metric="cosine", random_state=RANDOM_STATE),
        "hdbscan": dict(min_cluster_size=30, min_samples=10,
                        metric="euclidean", cluster_selection_method="eom"),
        "umap_2d": dict(n_components=2, n_neighbors=35, min_dist=0.0,
                        metric="cosine", random_state=RANDOM_STATE),
    },
    {
        "name": "tuned_stricter",
        "umap_5d": dict(n_components=5, n_neighbors=20, min_dist=0.05,
                        metric="cosine", random_state=RANDOM_STATE),
        "hdbscan": dict(min_cluster_size=40, min_samples=None,
                        metric="euclidean", cluster_selection_method="eom"),
        "umap_2d": dict(n_components=2, n_neighbors=20, min_dist=0.0,
                        metric="cosine", random_state=RANDOM_STATE),
    },
]

# -------------------------------------------------------------------
# Round-2 speaker mapping (stage 01e)
# -------------------------------------------------------------------
# Unresolved speech-prefix buckets (the `unresolved` lists in llm_maps/*.json)
# are ALWAYS kept on record in the maps and in extraction_merge_summary.xlsx.
# This switch only controls whether they enter character_table.csv — and thus
# embedding/clustering — as standalone pseudo-characters.
#   False (default): leave them out of clustering entirely (~0.14% of corpus words).
#   True:            include each unresolved form as its own row, named
#                    "[unresolved] <form>", e.g. after later fixing the <100-word
#                    leftovers and wanting to inspect what remains.
INCLUDE_UNRESOLVED_PREFIXES = False

# Speech-text normalization for character_table.csv (embedding input).
# The per-play JSONs and the plays sheet keep the VERBATIM transcription;
# this only cleans the text handed to the embedder, where printer-dependent
# typography would otherwise register as (spurious) style signal:
#   - long s (ſ) -> s                    (434k occurrences, 36% of characters)
#   - VV / Vv / vv -> W / w              (printers lacking a W sort)
#   - TCP damage/gap glyphs 〈◊〉 〈…〉 • ▪ removed (transcription noise)
# Deliberately NOT normalized (period-uniform or a research decision):
# u/v, i/j, ligatures (æ, œ), macron vowels (ā ō = suspended n/m).
NORMALIZE_SPEECH_TEXT = True

# Two speech-text versions are written by stage `table`:
#   character_table_original.csv  verbatim transcription (ſ, VV, damage glyphs
#                                 and all period spelling preserved)
#   character_table_modern.csv    typographic normalization + rule-based
#                                 spelling modernization driven by MorphAdorner's
#                                 EME resources (ememergedspellingpairs.tab,
#                                 standardspellings.txt)
# Both files contain the SAME rows (kept/dropped decided on the original text)
# so results are directly comparable. Stage 02 consumes the version named here:
TABLE_VERSION = "modern"          # "modern" | "original"
import os as _os
MORPHADORNER_DATA = Path(_os.environ.get(
    "MORPHADORNER_DATA",
    "/Users/heejin/Library/CloudStorage/Dropbox/Documents/Topics/"
    "Computational Analysis/Programs/MyPrograms/morphadorner-2.0.1/data"))
