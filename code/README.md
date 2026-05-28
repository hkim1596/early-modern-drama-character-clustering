# Character Clustering — pipeline

Cluster every named character in the matched early-modern drama corpus by the
full text of their speech (no chunking), and render the result as an
interactive map.

## Run order

```bash
python 01_normalize_characters.py
python 02_build_character_documents.py
python 03_embed.py                       # GPU server (gte-Qwen2-1.5B-instruct)
python 04_cluster.py
python 05_label_clusters.py
python 06_visualize.py
```

Stages 01, 02, 04, 05, 06 are CPU-bound and fast (minutes). Stage 03 is the
only GPU-bound step.

## Outputs

```
Character Clustering/
├── data/
│   ├── character_table.csv                # one row per (TCP, normalized_name) — speech text + match score
│   ├── name_normalization_review.csv      # borderline fuzzy matches for manual review
│   ├── dropped_short_characters.csv       # characters whose speech fell below the length cutoff
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
