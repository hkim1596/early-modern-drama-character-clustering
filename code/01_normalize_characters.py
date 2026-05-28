"""Stage 01 — Normalize character names against the British Drama catalogue.

For each play JSON in JSON_DIR:
  * Look up the play in the matched catalogue (by TCP id).
  * Parse the catalogue's `roles` field to get canonical role names + descriptions.
  * For every speech prefix in the JSON, fuzzy-match against the canonical names.
  * Aggregate speeches by normalized name; drop characters with very short text.

Outputs (in DATA_DIR):
  - character_table.csv           one row per (TCP, normalized_name)
  - name_normalization_review.csv borderline fuzzy matches for manual review
  - dropped_short_characters.csv  characters whose speech fell below the length cutoff
"""

from __future__ import annotations

import pandas as pd
from rapidfuzz import process, fuzz
from tqdm import tqdm

import config
from utils import (
    load_play_json,
    normalize_for_match,
    clean_speech_text,
    parse_roles_field,
)


def main() -> None:
    meta_df = pd.read_excel(config.META_XLSX)
    # Some catalogues have duplicate TCP rows; keep the first.
    meta_df = meta_df.drop_duplicates(subset=["TCP"]).set_index("TCP")
    print(f"📚 Catalogue: {len(meta_df)} plays (indexed by TCP)")

    json_files = sorted(config.JSON_DIR.glob("A*.json"))
    print(f"📄 Character JSONs found: {len(json_files)}")

    rows: list[dict] = []
    review_rows: list[dict] = []
    dropped_rows: list[dict] = []
    no_match_in_catalogue = 0

    for jf in tqdm(json_files, desc="Normalizing"):
        data = load_play_json(jf)
        tcp = data.get("tcp")
        if tcp not in meta_df.index:
            no_match_in_catalogue += 1
            continue

        meta_row = meta_df.loc[tcp]
        roles_str = meta_row.get("roles", "")
        catalogue_roles = parse_roles_field(roles_str)
        catalogue_names_norm = [normalize_for_match(r["name"]) for r in catalogue_roles]

        bucket: dict[str, dict] = {}
        for raw_name, speech in (data.get("speeches") or {}).items():
            raw_norm = normalize_for_match(raw_name)
            if not raw_norm:
                continue

            if raw_norm in config.GENERIC_LABELS:
                norm_name, description, score = "__crowd__", "", 100
            elif catalogue_names_norm:
                match = process.extractOne(
                    raw_norm, catalogue_names_norm, scorer=fuzz.token_set_ratio
                )
                if match is None:
                    norm_name, description, score = raw_name, "", 0
                else:
                    matched_str, score_value, idx = match
                    score = int(score_value)
                    if score >= config.NAME_MATCH_AUTO_THRESHOLD:
                        norm_name = catalogue_roles[idx]["name"]
                        description = catalogue_roles[idx]["description"]
                    elif score >= config.NAME_MATCH_REVIEW_THRESHOLD:
                        # Keep raw name to avoid merging distinct characters in
                        # the same play (e.g. Virginius vs Virginia). Just flag.
                        norm_name = raw_name
                        description = catalogue_roles[idx]["description"]
                        review_rows.append({
                            "TCP": tcp,
                            "raw_name": raw_name,
                            "suggested_match": catalogue_roles[idx]["name"],
                            "score": score,
                        })
                    else:
                        norm_name, description = raw_name, ""
            else:
                norm_name, description, score = raw_name, "", 0

            entry = bucket.setdefault(
                norm_name,
                {"raw_names": set(), "texts": [], "description": description, "score": score},
            )
            entry["raw_names"].add(raw_name)
            entry["texts"].append(speech or "")
            # Prefer the longest non-empty description we've seen
            if description and len(description) > len(entry["description"]):
                entry["description"] = description

        for norm_name, info in bucket.items():
            combined = clean_speech_text(" ".join(info["texts"]))
            n_chars = len(combined)
            n_words = len(combined.split())
            row = {
                "TCP": tcp,
                "normalized_name": norm_name,
                "raw_names": " | ".join(sorted(info["raw_names"])),
                "role_description": info["description"],
                "match_score": info["score"],
                "speech_text": combined,
                "n_chars": n_chars,
                "n_words": n_words,
            }
            if n_chars < config.MIN_SPEECH_CHARS or norm_name == "__crowd__":
                dropped_rows.append(row)
            else:
                rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(config.DATA_DIR / "character_table.csv", index=False)
    pd.DataFrame(review_rows).to_csv(
        config.DATA_DIR / "name_normalization_review.csv", index=False
    )
    pd.DataFrame(dropped_rows).to_csv(
        config.DATA_DIR / "dropped_short_characters.csv", index=False
    )

    print()
    print(f"✅ character_table.csv:               {len(df):>6} rows kept")
    print(f"   dropped_short_characters.csv:      {len(dropped_rows):>6} rows dropped")
    print(f"   name_normalization_review.csv:     {len(review_rows):>6} fuzzy matches flagged")
    print(f"   plays skipped (not in catalogue):  {no_match_in_catalogue:>6}")
    print(f"   plays included:                    {df['TCP'].nunique():>6}")


if __name__ == "__main__":
    main()
