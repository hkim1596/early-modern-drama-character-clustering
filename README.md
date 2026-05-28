# Early Modern Drama — Character Clustering

Unsupervised clustering of speaking characters in the early modern English dramatic repertoire by the full text of their speech. Each character is treated as a single document (no chunking), embedded with a long-context sentence encoder, and grouped by density-based clustering. The result is an interactive map of dramatic-character archetypes.

**Live visualization:** [view the interactive cluster map](https://hkim1596.github.io/early-modern-drama-character-clustering/) — replace this URL with the GitHub Pages address after you enable Pages.

## Method

1. **Corpus.** Plays drawn from EEBO-TCP and aligned to Martin Wiggins and Catherine Richardson's *British Drama: A Catalogue of Plays*. Bibliographic, genre, author, and date metadata merged from [DEEP](https://deep.sas.upenn.edu/) on `brit_drama_number`.
2. **Character extraction.** Speech prefixes in the play texts are normalized against the catalogue's role list (rapidfuzz, ≥ 92 = auto-merge), variants collapsed.
3. **Embedding.** Each character's full speech is encoded with `Alibaba-NLP/gte-Qwen2-1.5B-instruct` (32k-token context). No chunking — every word of the speech contributes to the character's vector.
4. **Clustering.** UMAP (5-D, cosine) → HDBSCAN (Euclidean, EOM) → UMAP (2-D) for visualization. Three parameter presets compared (`baseline`, `tuned_less_outliers`, `tuned_stricter`).
5. **Labels.** Per-cluster top words from class-based TF-IDF, after a stoplist that includes early-modern spelling variants.
6. **Visualization.** Interactive Plotly map; hover shows play / author / date / genre / role / cluster / top words. Dropdown menus highlight by decade, genre, author, play title, play type, or theater.

## Pipeline

```bash
python code/01_normalize_characters.py        # fuzzy-match speech prefixes to catalogue roles
python code/02_build_character_documents.py   # attach play metadata (joins on TCP)
python code/03_embed.py                       # GPU-recommended: gte-Qwen2-1.5B-instruct
python code/04_cluster.py                     # UMAP-5D → HDBSCAN → UMAP-2D, three presets
python code/05_label_clusters.py              # per-cluster top words (c-TF-IDF)
python code/06_visualize.py                   # interactive HTML per preset
```

Outputs land in `docs/` (HTML, served by GitHub Pages) and `data/` (CSVs and `.npy` files).

## Reproducing the data files

Several intermediate artifacts are excluded from the repo because of size (see `.gitignore`):

| File | Regenerate by | Notes |
|---|---|---|
| `data/character_json_all/` | external (EEBO-TCP extraction) | one JSON per play (TCP id) with `characters` + `speeches`. EEBO-TCP licensing applies. |
| `data/character_table.csv` | `01_normalize_characters.py` | ~35 MB |
| `data/character_documents.csv` | `02_build_character_documents.py` | ~87 MB |
| `data/embeddings.npy` | `03_embed.py` | ~75 MB, requires GPU |
| `data/cluster_xy_table__*.csv` | `04_cluster.py` | ~88 MB each |

## Requirements

```
pip install -r requirements.txt
```

The embedding step (`03_embed.py`) needs PyTorch + a CUDA-capable GPU (24 GB VRAM recommended for the 32k-token context window). All other stages run on CPU.

## Repository structure

```
.
├── code/                  # pipeline scripts (stages 01–06)
├── data/                  # metadata + small intermediate CSVs (large files gitignored)
├── docs/                  # GitHub Pages — interactive HTML maps
├── requirements.txt
└── README.md
```

## Citation

If you use this code or data, please cite this repository and the underlying sources:

- Wiggins, M. & Richardson, C., *British Drama 1533–1642: A Catalogue*. Oxford University Press, 2012–.
- DEEP: *Database of Early English Playbooks*. https://deep.sas.upenn.edu/
- EEBO-TCP: *Early English Books Online — Text Creation Partnership*.
- Li, Z., et al., *Towards General Text Embeddings with Multi-stage Contrastive Learning*. https://huggingface.co/Alibaba-NLP/gte-Qwen2-1.5B-instruct

## License

Code: MIT (or your preferred license).
Derived data files: subject to the EEBO-TCP and DEEP licensing terms of the originals.
