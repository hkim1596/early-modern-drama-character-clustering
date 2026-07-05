"""Build data/metadata.xlsx: one row per deep_tcp play, with catalogue data attached.

deep_tcp is the **spine**, so the metadata table is keyed per play-edition (per
TCP) — matching the single-play XML corpus. Only play records are kept
(record_type in {"Single-Play Playbook", "Play in Collection"}); the 36
"Collection" parent volumes and blank-type rows are excluded, because the corpus
has the individual plays, not the bound volumes.

The British Drama catalogue (``british_drama_matched_manual.xlsx``) is attached
by ``brit_drama_number``. Because one catalogue play can span several TCP
editions (e.g. Merchant of Venice: Q1 + Q2 + Folio), its catalogue entry is
**duplicated** onto each of those TCP rows — one row per edition, as intended.

Overlapping column names (TCP, stc, brit_drama_number) keep the deep_tcp value;
the catalogue's version gets a ``_bd`` suffix (TCP_bd, stc_bd). A
``catalogue_match`` column flags whether a deep_tcp row received catalogue data.

The script reports every mismatch:
  * deep_tcp play rows with NO catalogue entry (brit_drama_number absent from the
    catalogue) -> catalogue columns left blank.
  * catalogue plays that do NOT appear in the output (their brit_drama_number is
    on no deep_tcp play row) -> dropped, listed in full.
  * catalogue plays duplicated across multiple TCP editions -> informational.

Usage::

    python code/merge_metadata.py
    python code/merge_metadata.py --bd-xlsx <path> --deep-xlsx <path> --out <path>
    python code/merge_metadata.py --all-record-types   # keep Collections too

Dependencies: pandas, openpyxl.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
except ImportError:  # pragma: no cover
    sys.exit("This script needs pandas and openpyxl.\n  pip install pandas openpyxl")

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
DEFAULT_BD_XLSX = _ROOT / "data" / "british_drama_matched_manual.xlsx"
DEFAULT_DEEP_XLSX = _ROOT / "data" / "deep_tcp.xlsx"
DEFAULT_OUT_XLSX = _ROOT / "data" / "metadata.xlsx"

KEY = "brit_drama_number"
PLAY_RECORD_TYPES = ["Single-Play Playbook", "Play in Collection"]
_EXCEL_MAX = 32767  # Excel's per-cell character limit

# Catalogue columns worth surfacing near the front of the sheet.
_BD_FRONT = ["title", "roles", "plot"]
# deep_tcp columns worth surfacing near the front.
_DT_FRONT = ["TCP", "brit_drama_number", "record_type", "stc",
             "authors_display", "year_int", "genre_brit_display",
             "play_type_display", "item_title", "Title"]


def norm_key(series: "pd.Series") -> "pd.Series":
    """Normalize the join key: strip, drop a trailing '.0' (int-as-float), blank 'nan'."""
    return (
        series.astype(str).str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .replace("nan", "")
    )


def sanitize_for_excel(df: "pd.DataFrame") -> tuple["pd.DataFrame", int]:
    """Make every string cell safe for .xlsx: drop illegal control chars, cap length."""
    truncated = 0
    for col in df.columns:
        if df[col].dtype == object:
            cleaned = []
            for v in df[col]:
                if isinstance(v, str):
                    v = ILLEGAL_CHARACTERS_RE.sub("", v)
                    if len(v) > _EXCEL_MAX:
                        v = v[: _EXCEL_MAX - 1] + "…"
                        truncated += 1
                cleaned.append(v)
            df[col] = cleaned
    return df, truncated


def merge(bd_xlsx: Path, deep_xlsx: Path, out_xlsx: Path,
          all_record_types: bool = False) -> dict:
    bd = pd.read_excel(bd_xlsx, dtype=str).fillna("")
    dt = pd.read_excel(deep_xlsx, dtype=str).fillna("")

    dt_all_rows = len(dt)
    if not all_record_types:
        dt = dt[dt["record_type"].isin(PLAY_RECORD_TYPES)].copy()

    bd["_k"] = norm_key(bd[KEY])
    dt["_k"] = norm_key(dt[KEY])

    # Catalogue is per-play (per brit_drama_number). One row per key so a single
    # deep_tcp row cannot pick up two catalogue rows; the lone internal duplicate
    # (351, Gorboduc) is reported separately.
    bd_dup = bd[bd["_k"].duplicated(keep=False) & (bd["_k"] != "")][[KEY, "title", "TCP"]]
    bd_one = bd.drop_duplicates(subset="_k", keep="first")

    # deep_tcp is the spine; attach catalogue columns. deep_tcp keeps its own
    # TCP/stc; the catalogue's overlapping columns get a _bd suffix.
    merged = dt.merge(
        bd_one.drop(columns=["_k"]).rename(columns={KEY: KEY + "__bd_key"}),
        left_on="_k", right_on=KEY + "__bd_key", how="left", suffixes=("", "_bd"),
    )
    merged["catalogue_match"] = merged[KEY + "__bd_key"].notna() & (merged[KEY + "__bd_key"] != "")
    merged["catalogue_match"] = merged["catalogue_match"].map({True: "yes", False: "no"})
    merged = merged.drop(columns=[KEY + "__bd_key", "_k"])

    # Column order: key deep_tcp ids, catalogue text, match flag, then the rest.
    dt_front = [c for c in _DT_FRONT if c in merged.columns]
    bd_front = [c for c in _BD_FRONT if c in merged.columns]
    front = dt_front + bd_front + ["catalogue_match"]
    rest = [c for c in merged.columns if c not in front]
    merged = merged[front + rest]

    merged, truncated = sanitize_for_excel(merged)
    out_xlsx.parent.mkdir(parents=True, exist_ok=True)
    merged.to_excel(out_xlsx, index=False)

    # ---- report data ----
    dt_keys = set(dt["_k"][dt["_k"] != ""])
    # catalogue plays not represented on any deep_tcp play row -> dropped
    dropped = bd[~bd["_k"].isin(dt_keys)][[KEY, "title", "TCP"]]
    # catalogue plays duplicated across multiple TCP editions. Only count keys
    # that are REAL catalogue plays -- deep_tcp rows whose brit_drama_number is
    # placeholder text ("not in BritDrama", etc.) are not duplications, they are
    # simply no-catalogue rows (already counted in without_cat / MISMATCH 1).
    bd_keys = set(bd_one["_k"][bd_one["_k"] != ""])
    key_counts = dt[dt["_k"] != ""]["_k"].value_counts()
    multi_keys = key_counts[key_counts > 1]
    bd_titles = dict(zip(bd_one["_k"], bd_one["title"]))
    dup_across = [(k, bd_titles.get(k, ""), int(n))
                  for k, n in multi_keys.items() if k in bd_keys]
    dup_across.sort(key=lambda t: -t[2])

    return {
        "out": out_xlsx,
        "rows_out": len(merged),
        "cols_out": merged.shape[1],
        "dt_all_rows": dt_all_rows,
        "dt_spine_rows": len(dt),
        "with_cat": int((merged["catalogue_match"] == "yes").sum()),
        "without_cat": int((merged["catalogue_match"] == "no").sum()),
        "dropped": dropped,
        "dup_across": dup_across,
        "extra_rows_from_dup": int(sum(n - 1 for _, _, n in dup_across)),
        "bd_dup": bd_dup,
        "truncated": truncated,
        "all_record_types": all_record_types,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bd-xlsx", type=Path, default=DEFAULT_BD_XLSX)
    ap.add_argument("--deep-xlsx", type=Path, default=DEFAULT_DEEP_XLSX)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT_XLSX)
    ap.add_argument("--all-record-types", action="store_true",
                    help="Keep every deep_tcp row (incl. Collection parents), not just plays.")
    args = ap.parse_args()

    for p in (args.bd_xlsx, args.deep_xlsx):
        if not p.exists():
            sys.exit(f"Input not found: {p}")

    r = merge(args.bd_xlsx, args.deep_xlsx, args.out, args.all_record_types)

    scope = "ALL deep_tcp rows" if r["all_record_types"] else "deep_tcp PLAY rows (Single-Play + Play-in-Collection)"
    print(f"✅ {r['out'].name}: {r['rows_out']} rows × {r['cols_out']} columns")
    print(f"   spine = {scope}: {r['dt_spine_rows']} of {r['dt_all_rows']} deep_tcp rows")
    print(f"   rows WITH catalogue data : {r['with_cat']}")
    print(f"   rows WITHOUT catalogue   : {r['without_cat']}")
    print(f"   catalogue entries duplicated across editions: {len(r['dup_across'])} plays "
          f"(+{r['extra_rows_from_dup']} extra rows)")
    if r["truncated"]:
        print(f"   ⚠ cells truncated to Excel's 32767-char limit: {r['truncated']}")

    print(f"\n⚠ MISMATCH 1 — deep_tcp play rows with NO catalogue entry: {r['without_cat']} "
          f"(catalogue columns left blank)")

    print(f"\n⚠ MISMATCH 2 — catalogue plays NOT in the output ({len(r['dropped'])}; "
          f"their brit_drama_number is on no deep_tcp play row -> dropped):")
    for _, row in r["dropped"].iterrows():
        print(f"     {str(row[KEY]):>6}  {row['title']}  (cat TCP {row['TCP'] or '-'})")

    print(f"\nℹ catalogue plays duplicated across multiple TCP editions "
          f"({len(r['dup_across'])}; each becomes that many rows):")
    for k, title, n in r["dup_across"][:20]:
        print(f"     {k:>6}  ({n}×)  {title}")
    if len(r["dup_across"]) > 20:
        print(f"     … and {len(r['dup_across']) - 20} more")

    if len(r["bd_dup"]):
        print(f"\nℹ NOTE — brit_drama_number duplicated within the catalogue itself "
              f"({len(r['bd_dup'])} rows; first kept for the join):")
        for _, row in r["bd_dup"].iterrows():
            print(f"     {str(row[KEY]):>6}  {row['title']}  (TCP {row['TCP']})")


if __name__ == "__main__":
    main()
