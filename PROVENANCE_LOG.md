# PROVENANCE LOG — early-modern-drama-character-clustering

**Standing rules (set by Heejin, 2026-07-07 — binding on all future work):**

1. This project is for peer-reviewed publication. **No unrecorded editing of any kind.**
2. **No metadata change without Heejin's explicit approval.**
3. Editorial decisions (e.g. New Oxford Shakespeare canonical choices) may be adopted
   **only with an explicit note — never silently.**
4. Every data-affecting change is logged in this file, in the same commit as the change
   where possible.

---

## Entry 001 — retrospective record of assistant sessions, 2026-07-06 and 2026-07-07

Written 2026-07-07 by the assistant (Claude) at Heejin's request, covering everything
changed in the two working sessions after the June corpus update (`ce225d6`). One item
in §4e was made **without approval** and awaits a decision.

### 1. Session summary

Diagnosed and fixed a document-length confound in the character embeddings (whole-document
embeddings → 1,024-token chunked mean-pooled embeddings, re-embedded on the GPU server);
replaced the UMAP→HDBSCAN clustering (stage 04) with leave-one-out play centering +
spherical k-means; rebuilt stages 05–07 and the GitHub Pages site around the new typology;
added cast-confirmed edition deduplication applied at clustering time only; added
New Oxford Shakespeare canonical-edition overrides at Heejin's request.

### 2. Commit register (all pushed to `origin/main`)

Assistant commits unless marked [Heejin].

| commit | date | content |
|---|---|---|
| `73777bc` | 07-06 | Pipeline rewrite. 03: chunked embedding (1,024-token windows, token-weighted mean-pool; legacy whole-doc mode kept via `EMBED_CHUNK_TOKENS=None`; MPS fp16 + batch cap). 04: replaces UMAP→HDBSCAN presets with LOO play centering → linear length deflation → ≥150-word filter → spherical k-means (k=25) + k-sweep. 05–07: consume `config.CLUSTER_TABLES` instead of `PRESETS`. config: `PRESETS` removed; new knobs. |
| `2c9ac1d` | 07-06 | **Data:** `data/embeddings.npy` + `embeddings_metadata.json` replaced with the chunked re-embed (server GPU run, 15,734 chunks / 9,638 characters, 5 m 15 s). Whole-document originals preserved locally (untracked) as `data/embeddings_wholedoc.npy` + `embeddings_wholedoc_metadata.json`. |
| `6bde758…b48cf32` | 07-06 | Site regeneration #1 (7 commits): June HDBSCAN pages purged (36 cluster pages, 4,774 character pages, 3 preset maps), 25 new cluster pages + 7,339 character pages + archetype map; `utils.derive_display_columns()` introduced (§4a); landing page cards fixed. |
| `a4d113f…2a141f2` | 07-06 | Evidence pages v2 (7 commits): clean titles (§4a), curated archetype names (`data/cluster_names__archetype.json`), register keywords (§4c), chronological rosters with typicality, landmarks, per-cluster-trace map with working legend; fixed a long-standing bug that silently dropped all string metadata rows from character pages. |
| `66167e2` | 07-06 | Facet-split multi-valued filters: map dropdowns and cluster-page counts built from atomic facets of ';'-joined fields (§4a). |
| `a5c6fda` | 07-06 | Facet audit: "(?)" removed anywhere; ", trans./rev." author credits merged; pure-digit facets dropped; Company menu added. |
| `d1700d7` | 07-07 | Edition dedup **v1** (`work_id`/title grouping) in stages 02 + 04. Superseded — see §4b; the 02 half was later reverted (`7eae3f0`). |
| `3e6ae08…091aa09` | 07-07 | Re-cluster under dedup v1 + site regeneration (7,103 characters — the "(7,103 chars)" in this commit message is accurate **only for this chain**). |
| `e98674a` | 07-07 | Edition dedup **v2, cast-confirmed** after v1 was found to over-merge (§4b). |
| `80d5aa7…66fdea3` | 07-07 | Re-cluster under dedup v2 (6,453 characters) + site regeneration. ⚠ Commit message wrongly says "(7,103 chars)" — stale hard-coded message in the assistant's push script. |
| `7eae3f0` | 07-07 | Dedup made **clustering-time only** (stage-02 filter reverted — all editions now stay through table-building and embedding); `data/canonical_editions.json` added (§4d); stage 04 writes the inclusion/exclusion record `data/edition_dedup__<name>.csv`; **year imputation for undated canonical texts added — see §4e (unapproved)**. |
| `5e97fdc` | 07-07 | One-line dtype fix for the §4e year fill. |
| `5e5da07…f31dcfc` | 07-07 | [Heejin] Re-cluster with NOS overrides (6,467 characters) + cluster names re-curated by Heejin + site regeneration, pushed from her Mac using the assistant's push script. ⚠ Same stale "(7,103 chars)" message; actual run is 6,467. |

### 3. Data-file changes (beyond the commits above)

- **Replaced:** `data/embeddings.npy`, `data/embeddings_metadata.json` (chunked re-embed; `2c9ac1d`). Backup of the whole-document versions kept locally, untracked.
- **Regenerated repeatedly by pipeline stages:** `data/cluster_xy_table__archetype.csv` (git-ignored), `cluster_labels__`, `cluster_profiles__`, `cluster_summary__`, `cluster_k_sweep__archetype.*`.
- **Added:** `data/cluster_names__archetype.json` (curated names; current content by Heejin), `data/canonical_editions.json` (§4d), `data/edition_dedup__archetype.csv` (§4b record; regenerated by every stage-04 run).
- **Deleted (2026-07-06, obsolete HDBSCAN-era outputs, all regenerable):** `cluster_xy_table__{baseline,tuned_less_outliers,tuned_stricter}.csv`, `reduced_{2d,5d}__*.npy`, `clusters_hdbscan__*.npy`, `preset_summary.csv` (~495 MB), `code/__pycache__`, and the June site pages listed in the `b48cf32` chain.
- **Not modified at any point:** `data/character_documents.csv` (and .gz), `character_table_{original,modern}.csv`, `metadata.xlsx`, all raw JSON/XML corpora. The only source-adjacent change is the stage-02 code path (dedup filter added in `d1700d7`, **reverted** in `7eae3f0`; stage 02 was never actually re-run, so `character_documents.csv` on disk was never affected).

### 4. Editorial and metadata decisions

#### 4a. Display-layer transformations (presentation only — no stored data altered)

Applied at page/map build time by `utils.derive_display_columns()` / `utils.split_facets()`:

- **Play title:** use DEEP catalogue title (`item_title`, fallback `title.1`); else the raw title-page transcription with trailing TCP damage-glyph tokens stripped; else the TCP id. Raw transcription preserved in a `title_raw` column in memory; source columns untouched.
- **Author:** `authors_display` → `title_page_author` → `Author`; pure-digit junk values (e.g. "548") treated as missing; for *facet counts and filters only*: ";"-split, "(?)" markers removed, ", trans./rev./attrib." credits merged into the base author.
- **Genre / play type / company / theater facets:** ";"-split into atomic facets; "(?)" removed anywhere; "(on tour)"/"(in London)" qualifiers dropped; "(first)/(second)" identity qualifiers kept; pure-digit facets dropped.
- **Year (display):** bracketed catalogue dates ("[1544?]") parsed to their 4-digit year for sorting/display; `Date_Decade` derived from it.

#### 4b. Clustering-scope decisions (who is excluded from clustering; nothing deleted)

- `MIN_WORDS_CLUSTER = 150`: characters under 150 spoken words are not clustered (cluster = −1). Rationale: no stable stylistic signature; measured outlier rates were flat across length bands.
- **Edition dedup — v1 (`d1700d7`, superseded):** grouped by `work_id`, else title+author. **Found to over-merge:** the catalogue's `work_id` lumps distinct plays (four different Chapman comedies under one id; the "Antonio and Mellida ×5" group mixed part 1, its sequel, and reprints). Runs published under v1 (chain ending `091aa09`) therefore wrongly excluded some real plays; corrected in v2 the same day.
- **Edition dedup — v2/v3 (`e98674a`, `7eae3f0`, current):** every merge cast-confirmed by distinctive-name Jaccard (names in ≤15 plays): title+author equality (J ≥ 0.25); `work_id` only with same title or J ≥ 0.55; metadata-bare Folio/collection items by cast match (J ≥ 0.55; guarded fallbacks J ≥ 0.45 + margin, and sole-match ≥ 8 shared names for heavily divergent versions like Q1 Hamlet); near-identical casts under different titles (J ≥ 0.75 — catches catalogue mislabels: Jonson Works items with shifted titles, crossed item numbering in the two Alexander volumes). Verified: sequels (1H4/2H4, Promos 1/2), source plays (*Troublesome Reign* vs *King John*), and prequels (*1 Jeronimo*) all stay separate.
- **Recording:** since `7eae3f0`, every stage-04 run writes `data/edition_dedup__<name>.csv` — one row per edition of every multi-edition group: TCP, title, year, words, characters, included y/n, selection policy, kept edition. Current run: 59 works, 61 excluded editions, 872 excluded characters ≥150 words.
- **Default canonical choice:** earliest dated edition; ties by fullest transcription, then TCP id. Overridden per work by §4d.

#### 4c. Labeling pipeline (c-TF-IDF "distinguishing words")

Computed on the masked, spelling-modernized text (`speech_text_embedding` column — the same text the clustering uses), with: mask placeholders stopworded (someone / that place / foreign / the god); Latin and dialect function-word stoplists; a data-driven character-name blocklist (name tokens appearing in ≤4 plays' casts, plus 5-prefix i/j–u/v variant blocking). Some variant-spelled names still leak (e.g. "mephastophilis"); the systematic fix (stage-02 masking round 2 against cast lists) is proposed, not implemented.

#### 4d. Canonical editions — New Oxford Shakespeare (requested by Heejin 2026-07-07)

`data/canonical_editions.json` forces the kept edition per work, per Heejin's instruction
that NOS *Modern Critical Edition* choices are canonical for Shakespeare. Seeded by the
assistant as follows — **explicit note, per the standing rule**:

- Folio kept over a surviving "bad" quarto/octavo (the MCE base text or its nearest corpus witness): **Hamlet** (F over Q1 1603), **Romeo and Juliet** (F over Q1 1597), **Merry Wives** (F over Q 1602), **3 Henry VI** (F over O 1595).
- Two-text plays where the assistant's NOS reading should be **confirmed against the edition** (flagged `confirm: true` in the file): **King Lear** (F kept), **Othello** (F kept), **Richard III** (Q1 1597 kept), **Troilus and Cressida** (Q 1609 kept).

#### 4e. ⚠ UNAPPROVED — year imputation for undated canonical texts (`7eae3f0` + `5e97fdc`)

The Folio texts chosen in §4d carry no print year in the corpus metadata. To keep the
site's chronological rosters meaningful, the assistant added first-performance years from
`canonical_editions.json` into the `year` column **of the derived clustering table only**
(`cluster_xy_table__archetype.csv`) for those kept editions:

| TCP | work | imputed year |
|---|---|---|
| A11954.32 | Hamlet (F) | 1601 |
| A11954.28 | Romeo and Juliet (F) | 1595 |
| A11954.3 | Merry Wives (F) | 1597 |
| A11954.22 | 3 Henry VI (F) | 1591 |
| A11954.33 | King Lear (F) | 1606 |
| A11954.34 | Othello (F) | 1604 |

This conflates a print-year column with performance dating and was **not explicitly
approved** when introduced. `data/character_documents.csv` (the source) is untouched.

**RESOLVED 2026-07-07 — Heejin: "Keep, with explicit note."** The six imputed values
stay in the derived clustering table, documented here and in
`data/canonical_editions.json` as first-performance dating for undated Folio texts.
Optionally, site pages may mark these as "(perf.)" — not yet implemented; requires
separate approval.

### 5. Server actions (GPU server, khj container)

Chunked re-embed (07-06, GPU 1, 5 m 15 s; produced `2c9ac1d` data). Stage-04 runs on
07-07 producing the v1 (7,103), v2 (6,453) and NOS (6,467) tables, each pulled back by
SFTP with checksum verification. Residue on the server: `run04*.log`, `embed_chunked.log`,
`data/character_documents_audit.md.local` (renamed backup), regenerated stage-04 outputs.
No source data modified on the server.

### 6. Known record inaccuracies (cannot be fixed without history rewrite)

- Commit messages of `66fdea3` and `f31dcfc` say "7,103 chars"; the actual runs are
  6,453 and 6,467 respectively (stale hard-coded message in the assistant's batch-push
  script). The script should take the message as a parameter in future.
- The interpretive documents `Cluster_Analysis_2026-07-06.md` and
  `Archetype_Findings_2026-07-06.md` (project folder, outside the repo) describe the
  pre-dedup 7,339-character partition; both carry headers saying so.

---

## Entry 002 — 2026-07-07: canonical editions verified against the NOS Modern Critical Edition

Heejin placed her copy of *The New Oxford Shakespeare: Modern Critical Edition* (Taylor,
Bourus, Egan, Jowett eds.) in `References/`. The assistant extracted each play's "Text"
headnote and compared it with `data/canonical_editions.json`. Findings, with MCE quotes:

- **Verified correct (Folio-based per MCE):** Othello ("Based on the 1623 Folio… For the
  1622 text, see Alternative Versions"), Merry Wives ("The longer text edited here was
  first published in 1623"), 3 Henry VI ("Based on the 1623 Folio… the shorter,
  significantly different 1595 text" in Alternative Versions).
- **Corrected (previous assistant guesses were wrong):**
  - *King Lear* → **Q1 1608** kept (A11978): "based on the First Quarto of 1608, which
    gives the longest early text"; the Folio text is in Alternative Versions. The earlier
    Folio choice and its imputed year 1606 are withdrawn (Q1 is dated).
  - *Richard III* → **Folio** kept (A11954.23): "Based on the 1623 Folio"; Q 1597 is in
    Alternative Versions. Performance year 1592 imputed (NOS "Best guess 1592").
  - *Troilus and Cressida* → **Folio** kept (A11954.25): "based on the 1623 Folio"; the
    1609 edition is in Alternative Versions. Performance year 1602 imputed.
- **Nearest-witness inferences (MCE base absent from corpus), approved by Heejin:**
  Hamlet (MCE base Q2 1604–5; Q1 1603 and F both "Alternative Versions" — F kept as
  nearest witness) and Romeo and Juliet (MCE base Q2 1599; F kept, Q1 1597 short text).
- Consistent without overrides: Richard II, 1 Henry IV, 2 Henry IV (all Q-based per MCE;
  quartos already kept by the earliest-dated default).

Approvals (Heejin, 2026-07-07): apply all three corrections; keep Folio + explicit
inference note for Hamlet/Romeo; extend the approved performance-year convention to the
two newly kept Folio texts (R3 1592, Troilus 1602); re-run stages 04–07 now. Cluster ids
reshuffle on the re-run; Heejin's curated cluster names will be remapped by member
overlap and flagged for her review.

**Result (same day, commits `2ce3c7d` + `08a2b04`):** re-clustered with the verified
canon — 6,466 characters (59 works / 61 duplicate editions excluded; full record in
`data/edition_dedup__archetype.csv`, silhouette 0.021). The refit reorganized the
partition substantially; only 11 of Heejin's 25 cluster names could be transferred with
member-overlap ≥ 0.46 (transfer shares recorded in `cluster_names__archetype.json`).
The other 14 clusters (2, 3, 4, 9, 10, 11, 12, 14, 16, 18, 19, 21, 22, 23) carry
c-TF-IDF fallback labels on the site and **await Heejin's naming** against
`data/cluster_profiles__archetype.md`. No names were guessed. The batch-push script now
takes its commit message as a parameter (stale-message defect in §6 fixed).

---

## Entry 003 — 2026-07-07: full data verification (read-only; nothing changed)

Requested by Heejin after adding the original source files `data/DEEP_data.csv`,
`data/TCP.csv`, and `data/british_drama_matched_manual.xlsx` (collection volumes split
into per-play dotted TCPs manually by Heejin). Every check below was performed
read-only; **no data, metadata, or site file was modified**. This entry is the citable
verification record.

### Checks — all PASS

| # | check | result |
|---|---|---|
| 1 | Corpus coverage against `TCP.csv` (61,315 texts) | **PASS** — all 411 undotted corpus TCPs present; all 146 manually split dotted items have their parent volume present (33 collection volumes; largest: First Folio A11954 ×36, Jonson Works A72473 ×24 and A04632 ×21, Seneca *Tenne Tragedies* A11909 ×10) |
| 2 | Pipeline metadata against `DEEP_data.csv` (1,921 records) | **PASS** — 448/557 corpus plays carry a deep_id; all 448 resolve to a DEEP record (5 apparent misses were a float-formatting artifact, see F2); `item_title` and `year_int` are **100% identical** to DEEP on all matched plays |
| 3 | Manual match file coverage | **PASS** — 448/557 corpus plays present in `british_drama_matched_manual.xlsx`; the 109 absent plays are exactly the known metadata-bare set (mostly collection items) |
| 4 | `character_documents.csv` integrity | **PASS** — 9,638 rows; `character_id` unique; 557 plays; masked embedding text present for all rows; `n_words` > 0 everywhere; `mask_rate` ∈ [0,1] |
| 5 | `embeddings.npy` | **PASS** — shape (9,638 × 1,536) aligned with documents; no NaNs; all vectors L2-normalized; metadata records `mode: chunked`, 15,734 chunks |
| 6 | `cluster_xy_table__archetype.csv` | **PASS** — 9,638 rows in **identical order** to documents; clusters ∈ {−1…24}; 6,466 clustered / 3,172 not; x/y and `centroid_sim` present for exactly the clustered rows; `centroid_sim` ∈ [−1,1]; matches `cluster_summary__archetype.json` |
| 7 | Year imputations (approved, Entries 001–002) | **PASS** — imputed print-year values exist for **exactly** the seven kept Folio texts (3H6 1591, R3 1592, Wiv 1597, Romeo 1595, Hamlet 1601, Troilus 1602, Othello 1604; 181 character rows); no other undated row was touched; Lear correctly carries its real Q1 date 1608 |
| 8 | `edition_dedup__archetype.csv` record | **PASS** — 120 edition rows, 59 groups, exactly one included edition per group; all 61 excluded editions' 1,150 character rows have cluster = −1; the 8 canonical-override groups match `canonical_editions.json` |
| 9 | Labels / names / k-sweep | **PASS** — 26 label rows (−1…24); names json = 11 transferred names (Heejin's curation), 14 awaiting; k-sweep 9 rows |
| 10 | Site consistency | **PASS with finding F6** — 25 cluster pages; evidence lede says 6,466; but 7,339 character pages exist (see F6) |

### Findings (documented, NOT acted upon — each needs approval before any change)

- **F1.** `DEEP_data.csv` contains 69 ragged records (100 fields vs 99 in the header).
  Reference-file quality issue only; the pipeline's DEEP-derived values were verified
  100% identical to correctly parsed DEEP records.
- **F2.** `deep_id` is stored as a float in the pipeline metadata, so trailing zeros
  collapse ("5076.20" → "5076.2"; likewise 5081.10/.20/.30, 5124.20). All five such ids
  were verified to match the intended DEEP records (titles identical). Cosmetic;
  recommendation: store deep_id as a string at the next metadata rebuild.
- **F3.** **Alexander's two collection volumes (A16527 = *Monarchic Tragedies*;
  A16564 = *Recreations with the Muses*, 1637) have internally inconsistent item titles.**
  Cast evidence: A16527.1 (titled "The Alexandraean Tragedy", deep 5061.01) has a
  near-identical cast to A16564.1 (titled "Croesus", deep 5106.01), J = 0.91; the
  dedup's cast-based grouping merged them (and the .2/.3/.4 pairs) regardless of titles,
  so **clustering is unaffected**, but the title metadata of these 8 dotted TCPs is
  unreliable. DEEP's own export for 5061 lists two "Alexandraean Tragedy" items
  (Greg 260a(i)/(ii)) and no Croesus/Darius items, suggesting the source of confusion.
  → Flagged for Heejin's manual review of the A16527.x / A16564.x item assignments.
- **F4.** `british_drama_matched_manual.xlsx` has 467 rows but 455 unique TCPs
  (12 TCPs appear in multiple rows — presumably multi-work volumes). No action.
- **F5.** 109 corpus plays (19.6%) have no DEEP/manual-match metadata (titles fall back
  to TCP ids on the site) — the known metadata gap; enrichment would be a data change
  requiring approval.
- **F6.** `docs/characters/` contains **873 orphan pages** — stale pages generated for
  characters clustered in earlier, larger runs (7,339-character era) that are no longer
  clustered. They are not linked from any current page but remain reachable by direct
  URL with outdated cluster assignments. Deleting them is a site change awaiting
  approval. → **RESOLVED same day: Heejin approved deletion.** All 873 files removed;
  `docs/characters/` verified to contain exactly the 6,466 pages of the current
  partition (file set identical to the clustered character ids). The deleting commit's
  file list is the complete record of what was removed. Note: stage 07 does not prune
  stale pages automatically — adding that is a code change awaiting approval (§7).

---

## Entry 004 — 2026-07-10: names for the remaining 14 clusters (assistant-proposed at Heejin's request)

Heejin requested: "Give appropriate cluster names." The 14 clusters left unnamed after
the Entry-002 re-clustering (fallback c-TF-IDF labels) were named by the assistant from
recorded evidence — top and distinctive speaker names, c-TF-IDF register keywords, and
highest-typicality members — with the evidence stored per entry in
`data/cluster_names__archetype.json` (field `proposed`). Two names adapt Heejin's earlier
curation where the reading clearly matched ("Allegory, Nature & pageant voices";
"Law & judgment"). The 11 previously transferred names are unchanged. Stages 05–07
regenerated; site pushed (commit `7d2f33b`). These 14 names remain open to Heejin's
revision like any curation.

| id | name (proposed) | id | name (proposed) |
|---|---|---|---|
| 2 | Allegory, Nature & pageant voices | 14 | Law & judgment |
| 3 | Citizens, tradesfolk & neighbors | 16 | Errand servants & brief parts |
| 4 | Constant hearts & virtuous ladies | 18 | Chronicle statesmen & prelates |
| 9 | Boon companions & bluff banter | 19 | Grieving nobles & tragicomic sufferers |
| 10 | Mourners, mothers & doleful voices | 21 | Old fathers & plain counsel |
| 11 | Tosspots & tavern railers | 22 | Ghosts, curses & horror voices |
| 12 | Wooers, gallants & courtly love-talk | 23 | Gulls, fops & laughing-stocks |

---

## Entry 005 — 2026-07-10: manual metadata fills for TCP-titled plays + F3 resolution

Heejin: "I am seeing plays whose titles are TCP numbers. Can we fix them? … Let us figure
out here one by one." Of the 109 metadata-bare plays (F5), 58 are visible on the site.
All 58 received titles, with evidence, reviewed and **approved by Heejin as a batch
(Groups A–D)**; stored in `data/manual_metadata_fills.json` (evidence per entry) and
applied at page/map build time by `utils.derive_display_columns` — **display layer only;
no source file was modified**.

- **Group A (29):** undotted plays titled from their own title pages in `TCP.csv`
  (modern short titles proposed by the assistant; raw transcription kept as evidence).
  Includes *Ane Satyre of the Thrie Estaitis*, *The Antipodes*, *The Broken Heart*,
  *Aglaura*, *Everyman*, *The Cid*, Heywood interludes, and Caroline plays by
  Glapthorne, Nabbes, Lower, Berkeley, Freeman, Harding, Suckling, Shirley.
- **Group B (7):** the NOS-verified canonical Folio texts (Hamlet, Romeo, Wiv, 3H6, R3,
  Troilus, Othello) titled from their dedup groups.
- **Group C (22):** collection items identified by cast (unambiguous character sets):
  Jonson 1616/1631/1641 Works items (Every Man In (F), The Devil Is an Ass, The Magnetic
  Lady, eight masques/entertainments), Seneca *Medea* and *Hercules Oetaeus* (Tenne
  Tragedies), Alexander's *Julius Caesar*, *2 Troublesome Reign*, Medwall's *Nature*,
  *Of Gentleness and Nobility* 1–2. Years = parent-volume print years.
- **Group D (3) — F3 RESOLVED:** cast evidence + the 1607 title-page order
  ("Crœsus, Darius, The Alexandræan, Iulius Cæsar") establish that A16527.1 is
  **Croesus** (was mislabeled "Alexandraean") and A16527.3 is **The Alexandraean
  Tragedy** (was "Julius Caesar"; cast = Eumenes, Seleucus, Ghost of Alexander); and in
  Jonson's 1631 volume A04633.3 is **The Staple of News** (was "The Devil Is an Ass";
  cast = Pennyboy, Lickfinger). Corrections applied in the fills file (display layer);
  the underlying `item_title` columns remain as-is in source files.
- Also noted: A04632.10 / A04637.1 are the same work (the 1604 King's Entertainment) in
  two printings — too few distinctive names for the cast-dedup to merge automatically;
  left as two entries, flagged for a possible future dedup decision.
- Remaining bare plays: 51, none visible on the site (excluded duplicates or
  below-threshold only).

Site regenerated (map + all pages); pushed with the fills file and this entry.

---

## Entry 006 — 2026-07-10: Tier-1 evidence-page update (approved)

Heejin approved implementation of Tier 1 (items 1.1–1.7) of
`Evidence_Pages_Update_Proposal_2026-07-10.md` (project root): "I approve Tier 1 in one
05/07 pass (1.1–1.7)." Implemented by the assistant the same day. **Only
`code/07_generate_site.py` needed changes** (05 required none — curated fields are read
directly from the names JSON at page-build time). No source data file was modified; the
names JSON gained one documentation key (below). Character pages are untouched by any of
this (their template did not change); a `--no-characters` flag was added to stage 07 so a
cluster-page-only regeneration is possible without rewriting 6,466 unchanged files.

What the regenerated cluster pages + master index now show:

1. **Reading-guidance banner (1.1)** on all 25 cluster pages + index: partition identity
   ("2026-07-07 NOS-verified run", k/seed/n and silhouette read from
   `cluster_summary__archetype.json`) and the continuum framing (RQ1/RQ30). Seed-to-seed
   ARI 0.29 (0.26–0.35) is quoted from Clustering_Results_Report_2026-07-08 (it is not in
   any data file) — noted in a code comment; re-measure after any re-cluster.
2. **Name-status badges (1.2)**: the 14 assistant-proposed names (Entry 004) render
   "name proposed — pending curation" (tooltip = the recorded evidence); the index carries
   a matching marker + legend. Removing/replacing the `proposed` field clears the badge.
3. **Historical profile (1.3)**, promoted out of `<details>`: paired 5-year-bin share
   bars (cluster vs corpus), median / pre-1590 / post-1625 with ×lift vs corpus.
   **Year basis**: the performance year as catalogued (numeric parse + 4-digit
   extraction), EXCLUDING the Entry-005 display-layer fill years (parent-volume print
   years, late-skewed) — this reproduces the report's dated base exactly
   (n=6,040, median 1611, pre-1590 8.6%, post-1625 31.8%). Roster/landmark Year columns
   keep the display year; the page says so.
   **Badge rules** (≥20 dated members): early-rooted = pre-1590 share ≥1.40× corpus;
   late register = post-1625 share ≥1.15× corpus AND median > corpus median. On this
   partition: early-rooted → cl2 (×2.01), cl15 (×1.59), cl22 (×1.59), cl11 (×1.49) —
   the report's list — plus cl23 (×1.43), which qualifies under the rule though the
   report quoted only the top four; late register → cl20/cl19/cl4, matching the report.
4. **Signature panels (1.4)**: authors / genres / companies / theaters / play types as
   ×lift vs the clustered corpus (share-of-members basis, facets atomized by
   `utils.split_facets`; authors need n≥4, other facets n≥5, lift ≥1.2, top 5).
   Verified against the report: cl19 Massinger ×3.00, Field ×3.51, Tragicomedy ×2.09;
   cl24 Masque ×3.09 (report: 3.0 / 3.5 / 2.1 / 3.1). Raw counts remain in the
   collapsed details.
5. **Curated interpretation fields (1.5)**: optional per-cluster `historical_types`,
   `note`, `criticism` and top-level `families`, `attested_types` in
   `cluster_names__archetype.json` render when present (nothing curated yet, so nothing
   renders); a `_schema` key documenting them was added to the JSON — the only change to
   that file; all 25 entries untouched.
6. **Excerpt provenance (1.6)**: each representative excerpt now carries
   typical/early/familiar chips explaining why it was sampled; the distinguishing-
   vocabulary lede carries a caveat that name-like tokens are masking residue (until the
   §7.3 masking round 2); optional curated `display_keywords` per cluster replace the
   lede list when present (the algorithmic list then moves to the collapsed details and
   still drives excerpt highlighting).
7. **Index upgrades (1.7)**: median year + decade sparkline per card; family-description
   and attested-type-coverage sections render once curated.

Verification (cloud re-run against published outputs, pandas 2.2.3): corpus baselines
and all quoted lifts match the 2026-07-08 report to rounding, as listed above. Scope of
regeneration: `docs/cluster_00.html`–`cluster_24.html` + `docs/cluster_evidence.html`
(26 files); `docs/index.html`, the map, and `docs/characters/` untouched. The open
"(perf.)" year-marker item (§7.3) was NOT implemented — it remains awaiting its own
approval.

---

## Entry 007 — 2026-07-10: emergence + prototype labels replace the "early" badges; performance-first roster dating; methods page (approved)

Heejin asked what "the earliest members (early)" are, noted they were counted
"regardless of typicality scores," and requested a more optimal method — identify when
each cluster meaningfully emerged, then identify archetype/prototype members — plus a
page explaining how the labels are computed. Four decisions were put to her and
approved the same day: (1) emergence + typicality-gate method; (2) performance-first
year basis for the genealogical elements; (3) roster re-dated to performance-first;
(4) concise one-page methods page. Implemented in `code/07_generate_site.py` only.

**Defect in the old rule (measured on this partition).** "early" = the first 5 dated
roster rows in display-year order, typicality ignored; the page called them "the
candidate prototypes of this voice." Those five sat at the **35th typicality percentile**
of their cluster on average; in 16/25 clusters at most one reached the cluster median
(in 5 clusters none); ties at the 5-boundary were broken arbitrarily by word count; and
Entry-005 display fill years counted as dates.

**New dating columns (display/derived layer only; no source file modified).**
- `year_perf` = parsed `date_first_performance` (numeric, else first 4-digit run;
  values outside 1400–1700 treated as missing). Covers 5,911 of 6,466 clustered
  characters (91.4%). Performance years run a median of 3 years earlier than the print
  year (mean ≈ 6.8; e.g. *The Spanish Tragedy* 1592 → 1587); 0.3% parse later.
- `year_gen` = `year_perf` else the catalogued year (`year_analysis`): the ANALYSIS
  basis for emergence/prototypes, 6,040 dated members; Entry-005 fill years never enter.
- `year_roster` = `year_gen` else the display fill year: what rosters display/sort by.
The performance datings are the DEEP catalogue's editorial datings, adopted here with
this explicit note (standing rule 3). The published report keeps the print-year basis;
each page element now states its basis, and the historical-profile strip + its
early-rooted/late-register badges are **unchanged** (catalogued basis, still reproducing
the report: dated n=6,040, median 1611, pre-1590 8.6%, post-1625 31.8%).

**Emergence + prototype rules (constants `EMERGE_*`, `PROTO_*` in 07).** Per cluster
with ≥20 `year_gen`-dated members: *first recorded* = earliest dated member;
*established by* = the year the first tenth (⌈10%⌉) of dated members had appeared;
*formative era* = members dated up to that year (tinted rows); *prototype* = formative
member with `centroid_sim` ≥ the cluster median, top 5 by typicality — badged in the
roster, shown first among landmarks and excerpts (chips now read prototype/typical/
familiar). Simple sustained-window rules ("first decade with ≥3 members, recurring")
were tested and **rejected**: they collapse to the corpus onset (1544–84) for nearly
every cluster — they track playbook survival, not the type's take-off. Prototype badges
assert kinship and corpus priority, not proven indebtedness (the temporal kNN genealogy
remains the planned lineage instrument, proposal Tier 3.1).

**Also switched to performance-first on cluster pages/index:** roster Year column +
sort, header date range, landmark/excerpt/exemplar years, index card ranges + medians +
new "est. by YYYY", decade sparklines, collapsed decade bars (labeled). Character pages
are untouched this pass (still catalogued year; noted on the methods page) — their
template did not change and they were not regenerated.

**New `docs/methods.html`** (concise one-pager): pipeline summary and how every on-page
number/badge is computed (typicality, the three year bases, emergence, prototype,
early-rooted/late register, ×lift signatures, c-TF-IDF vocabulary + masking-residue
caveat, name curation/proposed badges), plus a "what these pages do not claim" section
(survival ≠ production; priority ≠ influence; membership ≠ essence). Linked from the
reading banner, roster ledes, strip axis note, index lede, and page footers.

**Emergence values published by this run (performance-first; first / established by,
dated n):** cl00 1550/1589 (307) · cl01 1528/1589 (284) · cl02 1528/1565 (273) ·
cl03 1528/1581 (266) · cl04 1538/1590 (264) · cl05 1553/1589 (267) · cl06 1538/1588
(259) · cl07 1537/1583 (247) · cl08 1538/1588 (255) · cl09 1538/1590 (256) ·
cl10 1537/1575 (256) · cl11 1537/1577 (242) · cl12 1528/1589 (245) · cl13 1553/1590
(241) · cl14 1538/1578 (221) · cl15 1528/1567 (227) · cl16 1528/1576 (224) ·
cl17 1550/1588 (223) · cl18 1537/1590 (225) · cl19 1550/1587 (228) · cl20 1528/1584
(227) · cl21 1528/1584 (214) · cl22 1537/1577 (213) · cl23 1537/1578 (204) ·
cl24 1560/1585 (172). Like cluster names, these are partition-bound and stale after any
re-cluster.

**Verification (cloud re-run against the published table, pandas 2.2.3).** Prototype
lists match the calibration run — cl5 Romantic leads: Pythias (*Damon and Pithias*,
perf 1564), Tellus (*Endymion*, 1588), Alvida (*A Looking Glass*, 1588), Cornelia
(*Wounds of Civil War*, 1588), Margaret (*Friar Bacon*, 1589); cl22 Ghosts/horror:
God's Vengeance (Bale, *Three Laws*), Conscience (*Appius and Virginia*), Nature
(*Interlude of Vice*), Horror (*Conflict of Conscience*), Damnation (*All for Money*).
Historical-profile numbers unchanged in basis (cl5: 267 dated of 281, median 1609 vs
corpus 1611). No stale "early" badges remain; `docs/characters/` untouched.

**Scope of this commit:** `code/07_generate_site.py`, `docs/cluster_00–24.html` (25),
`docs/cluster_evidence.html`, `docs/methods.html` (new), this log. No data file changed.

---

## Entry 008 — 2026-07-10: site redesign ("clean modern academic"), shared stylesheet, generated landing page (approved; presentation-only)

Heejin: "The design of the web page is not really organized. Make it more pleasing as
well as organized design wise." Two recorded choices: direction = **clean modern
academic** (over a serif "scholarly print edition" and a bolder editorial option);
scope = **full site including the 6,466 character pages, via a shared stylesheet**.

- All styling moved out of per-page inline `<style>` blocks into **`docs/site.css`**,
  written by stage 07 (single source of truth — future redesigns touch one file, not
  6,500). Every page gains a sticky masthead (Map · Clusters · Methods · GitHub), a
  typographic scale, and one unified badge/chip palette (prototype violet · typical
  blue · familiar gray · time amber · proposed orange — previously four ad-hoc schemes).
  Rosters get sticky column headers under the masthead; formative-era rows keep their
  tint plus an accent edge; layout is responsive.
- Cluster-page header reorganized (presentation only): title → vocabulary lede → fact
  strip (characters / plays / authors / year span / **est. YYYY**) → reading banner →
  curated block. The establishment year is thereby surfaced as a headline figure. No
  displayed value, rule, or computation changed.
- **`docs/index.html` is now generated** by 07 (`render_landing_page`); it was a
  hand-maintained static file. Prose refreshed with approval-consistent semantics: the
  stale pre-Entry-007 sentence ("the earliest members are the candidate prototypes of
  that voice") is retired in favor of the emergence/prototype wording; a Methods entry
  card and dynamic corpus numbers (from the published table at build time) added.
- **Character pages regenerated** (all 6,466): masthead + stylesheet link; the metadata
  table's "Year" row is relabeled "Year (catalogued)" and a "**First performance**" row
  (parsed `year_perf`, where the catalogue records one) is added — the Entry-007 dating
  extended to character pages at their promised "next regeneration"; the cluster label
  no longer doubles its id prefix ("Cluster 22 — 22: …" → "Cluster 22 — …"). The
  methods-page sentence about character-page dating updated to match.
- Verification: full rebuild reproduces Entry-007 values exactly (emergence table
  identical; cl5 prototypes Pythias/Tellus/Alvida/Cornelia/Margaret; historical-profile
  stats unchanged). Pages rendered and visually inspected (landing, index, cluster,
  roster mid-scroll, character, methods) before shipping.
- **Scope of this commit:** `code/07_generate_site.py`, `docs/site.css` (new),
  `docs/index.html`, `docs/methods.html`, `docs/cluster_00–24.html`,
  `docs/cluster_evidence.html`, `docs/characters/*.html` (6,466), this log.
  No data file changed. The interactive map file is untouched.

---

## Entry 009 — 2026-07-10: the fourteen assistant-proposed cluster names approved by Heejin (Entry 004 closed)

Heejin approved all fourteen assistant-proposed names (Entry 004: clusters 2, 3, 4, 9,
10, 11, 12, 14, 16, 18, 19, 21, 22, 23) — approval executed in a **parallel working
session** on 2026-07-10 and confirmed by Heejin in this session ("I think I approve
those names in another session"). All 25 cluster names are now Heejin's curation.

What the parallel session changed in `data/cluster_names__archetype.json` (verified
here against the committed version before adoption): names and families of all 25
clusters **byte-identical**; the 14 `proposed` flags removed; each cluster's drafting
evidence preserved verbatim in a new `name_provenance` field with "; approved by
Heejin 2026-07-10 (…)" appended; an update note added to `_note`. File reformatted
(indent width) by that session's JSON writer.

**Numbering reconciliation.** The parallel session's update note cited "PROVENANCE_LOG
Entry 008", and its own log entry — if it wrote one — was overwritten by this session's
concurrent Entry-008 (site redesign) commit `7eecf77`, which bridged the log file
without a staleness guard. This entry reconstructs the approval record; the only edit
made to the approved json here is correcting that one citation to Entry 009 (recorded
in the `_note` itself). Lesson noted: cross-session commits to this log must re-stage
the current on-disk log first.

**Site effect:** the "name proposed — pending curation" badges and the index legend
clear (they render from the `proposed` field). Cluster pages + master index
regenerated; character pages and all computed values untouched. §7 item 5 (names
awaiting Heejin) is closed.

**Scope of this commit:** `data/cluster_names__archetype.json`,
`docs/cluster_00–24.html`, `docs/cluster_evidence.html`, this log.

---

### 7. Open items requiring explicit approval before any action

1. ~~§4e year imputation~~ — **resolved 2026-07-07: keep, with explicit note** (recorded
   in §4e and `canonical_editions.json`).
2. ~~§4d `confirm: true` NOS entries~~ — **resolved 2026-07-07 (Entry 002)**: verified
   against Heejin's MCE copy; Lear/R3/Troilus corrected with approval.
3. Proposed but NOT implemented: stage-02 masking round 2 (fuzzy cast-list matching);
   metadata source fixes (digit junk in `authors_display`, deep_id float→string (F2),
   ~20% missing DEEP titles (F5)); consensus clustering; fixed-budget chunk pooling
   experiment; "(perf.)" year marker on site pages for the §4e values.
4. ~~Committing and pushing this log file~~ — **approved 2026-07-07**.
5. ~~Cluster names for ids 2, 3, 4, 9, 10, 11, 12, 14, 16, 18, 19, 21, 22, 23~~ —
   **resolved 2026-07-10 (Entry 009): all fourteen approved by Heejin.**
6. ~~A16527.x / A16564.x item-title assignments~~ — **resolved 2026-07-10 (Entry 005,
   Group D)**: cast + title-page evidence; corrections applied at display layer.
7. ~~873 orphan character pages in `docs/characters/`~~ — **resolved 2026-07-07:
   deletion approved and executed** (F6; file list in the deleting commit).
8. Stage 07 auto-pruning of stale character pages on each run — code change awaiting
   approval.
