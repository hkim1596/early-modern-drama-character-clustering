"""Stage 02 — Attach play-level metadata to each character row.

Reads the consolidated metadata.csv (built by merging british_drama_matched_cleaned.xlsx
and deep_tcp.xlsx on brit_drama_number). Joins on TCP, applies light cleaning, and
emits character_documents.csv — one row per character, with all metadata.

Inputs (in DATA_DIR):
  - character_table.csv   (from stage 01)
  - metadata.csv          (consolidated play-level metadata)

Outputs (in DATA_DIR):
  - character_documents.csv
"""

from __future__ import annotations
import re
import pandas as pd

import config


def collapse_ws(s):
    """Collapse runs of whitespace (incl. embedded newlines) into single spaces."""
    if not isinstance(s, str):
        return s
    return re.sub(r"\s+", " ", s).strip()


def canonical_display_name(name: str) -> str:
    """Display character names in catalogue convention: ALL CAPS, no mid-word lowercase.

    The British Drama catalogue uses ALL-CAPS for role names. Our parser sometimes
    extracts mixed-case forms ("vIRGINIUS") because the OCR introduced a stray lowercase
    leader. Uppercasing produces a clean canonical display form that matches the
    catalogue's convention.
    """
    if not isinstance(name, str):
        return name
    # Generic/crowd buckets stay lowercase + bracketed
    if name == "__crowd__":
        return "[crowd]"
    return name.upper().strip()


def main() -> None:
    char_df = pd.read_csv(config.DATA_DIR / "character_table.csv")
    if not config.METADATA_CSV.exists():
        raise FileNotFoundError(
            f"{config.METADATA_CSV} not found. Build it first by merging "
            f"british_drama_matched_cleaned.xlsx and deep_tcp.xlsx on brit_drama_number."
        )
    meta = pd.read_csv(config.METADATA_CSV)
    print(f"📚 Loaded metadata.csv: {len(meta)} plays, columns: {list(meta.columns)}")

    # ---- Join on TCP ----
    merged = char_df.merge(meta, on="TCP", how="left", suffixes=("", "_meta"))
    matched = merged["title"].notna().sum()
    print(f"📎 Characters matched to metadata: {matched}/{len(merged)}  ({matched/len(merged):.0%})")

    # ---- Cleaning passes ----
    # Uppercase display name (catalogue convention) — kept separately so analytic code
    # can still join on `normalized_name` if needed.
    merged["display_name"] = merged["normalized_name"].apply(canonical_display_name)

    # Collapse newlines that linger inside role_description
    if "role_description" in merged.columns:
        merged["role_description"] = merged["role_description"].apply(collapse_ws)

    # plot is already collapsed when metadata.csv was built; defensive collapse anyway
    if "plot" in merged.columns:
        merged["plot"] = merged["plot"].apply(collapse_ws)

    # ---- Stable character_id (TCP::DISPLAY_NAME) ----
    merged["character_id"] = (
        merged["TCP"].astype(str) + "::" + merged["display_name"].astype(str)
    )

    # ---- Column ordering ----
    front = [
        "character_id", "TCP", "brit_drama_number",
        "display_name", "normalized_name", "raw_names",
        "title", "author", "year", "Date_Decade",
        "date_first_performance", "genre", "play_type",
        "theater", "theater_type", "company",
        "role_description", "match_score",
        "n_chars", "n_words",
    ]
    front = [c for c in front if c in merged.columns]
    rest  = [c for c in merged.columns if c not in front and c != "speech_text"]
    cols  = front + rest + (["speech_text"] if "speech_text" in merged.columns else [])
    merged = merged[cols]

    out_path = config.DATA_DIR / "character_documents.csv"
    merged.to_csv(out_path, index=False)
    print(f"\n✅ {out_path.name}: {len(merged)} rows, {len(merged.columns)} columns")
    print(f"   Columns: {list(merged.columns)}")

    # Coverage check on the fields the visualization uses
    print(f"\n   Hover-field coverage:")
    for c in ["title", "author", "year", "Date_Decade", "genre", "play_type", "theater", "role_description"]:
        if c in merged.columns:
            n = merged[c].notna().sum()
            print(f"     {c:25s} {n:5d}/{len(merged)}  ({n/len(merged)*100:.0f}%)")


if __name__ == "__main__":
    main()
