# Character Clustering — pipeline

Cluster every named character in the matched early-modern drama corpus by the
full text of their speech (no chunking), and render the result as an
interactive map.

## Run order

```bash
python 01_build_corpus.py                # extract + summary + character table
python 02_build_character_documents.py
python 03_embed.py                       # GPU server (gte-Qwen2-1.5B-instruct)
python 04_cluster.py
python 05_label_clusters.py
python 06_visualize.py
```

Stage 01 is unified: XML extraction, the speaker-map summary (validation +
verify flags included), and the character table all run from one script and
share ONE bookkeeping workbook, `data/corpus_master.xlsx` (sheets: plays,
speaker_maps, extraction, characters, decisions, queue). The `speaker_maps`
sheet is the single source of mapping truth — edit it, then rerun
`python 01_build_corpus.py --stage summary` and `--stage table`. Unresolved
prefix buckets are excluded from clustering (config.INCLUDE_UNRESOLVED_PREFIXES
toggles this); they appear on the `characters` sheet as `unresolved_excluded`.
Superseded stage-1 scripts and the old multi-file bookkeeping live in
`_superseded_stage1/` (safe to delete).

Stages 01, 02, 04, 05, 06 are CPU-bound and fast (minutes). Stage 03 is the
only GPU-bound step.

## Outputs

```
Character Clustering/
├── data/
│   ├── corpus_master.xlsx                 # ALL stage-1 bookkeeping (plays / speaker_maps / extraction / characters / decisions / queue)
│   ├── character_table_original.csv       # kept characters, VERBATIM transcription (ſ, VV, damage glyphs preserved)
│   ├── character_table_modern.csv         # same rows, typographic normalization + MorphAdorner rule-based spelling modernization (config.TABLE_VERSION picks which one stage 02 uses)
│   ├── character_documents.csv            # character_table + play metadata (title, author, genre, date, plot, …)
│   ├── embeddings.npy                     # [n_characters, dim] aligned 1-to-1 with character_documents.csv
│   ├── embeddings_metadata.json
│   ├── reduced_5d__<preset>.npy
│   ├── reduced_2d__<preset>.npy
│   ├── clusters_hdbscan__<preset>.npy
│   ├── cluster_xy_table__<preset>.csv     # master table: documents + x/y + cluster + topic_label + top_words
│   ├── cluster_labels__<preset>.csv       # per-cluster top distinguishing words (c-TF-IDF) + members
│   └── preset_summary.csv                 # summary stats per preset
└── results/
    └── interactive_clusters__<preset>.html
```

## Configuration

All paths and hyperparameters live in `config.py`. To run on a different
machine without editing the file, set the base directory at the command line:

```bash
CHAR_CLUSTERING_BASE=/home/khj/character_clustering python 03_embed.py
```

## Embedding model

Default: `Alibaba-NLP/gte-Qwen2-1.5B-instruct` (32k-token context — handles a
character's full speech without truncation in virtually all cases). On an
RTX 6000 / A6000, fp16/bf16 inference uses ~3 GB of weights plus modest
activation memory; flash-attention 2 is optional but recommended for the
longest documents.

To swap models, change `EMBED_MODEL` in `config.py`. Long-context alternatives
worth considering: `nomic-ai/nomic-embed-text-v1.5` (8k), `jinaai/jina-embeddings-v3`
(8k), OpenAI `text-embedding-3-large` (8k, API).

## Dependencies

```bash
pip install -r requirements.txt
# GPU server, recommended additions:
pip install accelerate
pip install flash-attn --no-build-isolation
```
