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
# Sized to hold the corpus's longest character untruncated: CELESTINA
# (A18331, The Spanish Bawd) is 37,936 tokens incl. the instruction prefix.
# gte-Qwen2 is tuned for a 32k context but supports up to 131072 positions
# (rope_theta=1e6, patched in 03_embed.py), so we can go past 32k rather than
# drop text. 03_embed.py aborts if ANY document still exceeds this — never
# silently truncates. Raise further (or chunk) if a longer character appears.
EMBED_MAX_TOKENS = 40960
EMBED_BATCH_SIZE = 1       # safe default for long inputs; raise if VRAM allows
EMBED_INSTRUCTION = "Represent the unique speech style and rhetorical signature of this dramatic character for similarity comparison."

# --- Chunked embedding (2026-07: fixes the length confound) ---
# Diagnosis on the first full run: log(word count) was recoverable from the
# top-5 PCs of the whole-document embeddings with R²=0.90 — the space was
# organized by document LENGTH, not by character. One embedding per character
# over docs ranging 53 words – 38k tokens bakes length/register into the
# vector. Fix: split each character's speech into ~EMBED_CHUNK_TOKENS windows
# (token-aligned, tail <25% merges into the previous window), embed each
# window, then token-weighted mean-pool + L2-normalize per character. Every
# character is then represented in the same length regime — and CELESTINA no
# longer needs a 40k context (EMBED_MAX_TOKENS only applies to the legacy
# whole-doc mode).
# Set EMBED_CHUNK_TOKENS = None to reproduce the legacy whole-document
# embeddings (kept for control comparison).
EMBED_CHUNK_TOKENS     = 1024
EMBED_CHUNK_BATCH_SIZE = 16    # chunks are short; raise/lower to fit VRAM

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
# Clustering (stage 04: LOO play centering + spherical k-means)
# -------------------------------------------------------------------
# The original UMAP→HDBSCAN preset pipeline was retired 2026-07-06 (length
# confound + wrong tool for a typology; see 04_cluster.py docstring and git
# history for the old presets).
RANDOM_STATE = 42

# Cluster-table name suffixes consumed by stages 05–07
# (cluster_xy_table__<name>.csv). Stage 04 writes CLUSTER_TABLES[0] by
# default; add entries here when comparing runs (e.g. a whole-document
# control re-run of stage 03).
CLUSTER_TABLES = ["archetype"]

# Edition deduplication — CLUSTERING-TIME ONLY. All editions are kept through
# table-building (stage 02) and embedding (stage 03) so alternative editions
# remain available for comparison work; stage 04 excludes duplicates at the
# last minute (cluster = -1) because duplicated characters inflate clusters
# and corrupt the temporal genealogy (a character's nearest neighbour becomes
# its own reprint). Grouping is cast-confirmed (utils.canonical_edition_tcps);
# the default choice is the earliest dated edition, overridden per work by
# data/canonical_editions.json (New Oxford Shakespeare Modern Critical Edition
# choices for Shakespeare). Stage 04 writes the full inclusion/exclusion
# record to data/edition_dedup__<name>.csv.
DEDUPE_EDITIONS = True

# Characters below this many words don't carry a stable stylistic signature
# (and are mostly functional bit-parts). Filtering happens at CLUSTERING time,
# not at table-build time, so the documents table keeps every character.
# 150 keeps ~7.3k of 9.6k characters and ~98% of corpus words.
MIN_WORDS_CLUSTER = 150

# Linear length-axis deflation applied after play-centering. Needed while
# embeddings.npy is still the legacy whole-document run (length R² 0.90 →
# ~0.33 after centering+3 rounds). After re-embedding with
# EMBED_CHUNK_TOKENS set, this should do little — set to 0 and check that the
# reported length R² stays low on its own.
LENGTH_DEFLATE_ROUNDS = 3

# k for the final partition. The k-sweep (silhouette diagnostics over
# KMEANS_K_SWEEP) is written alongside; pick k by silhouette + interpretability
# of the profiles, not silhouette alone (it tends to favor degenerate small k).
KMEANS_K       = 25
KMEANS_K_SWEEP = [10, 15, 20, 25, 30, 35, 40, 50, 60]

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
