"""Staging and commit logic for the two-step upload workflow.

Records flow:  Upload -> Stage (preview) -> Commit (update dashboard)
               or       Upload -> Stage (preview) -> Cancel (discard)

Data management:  List committed records -> Delete -> Recompute emissions
"""

import json
import os
import uuid
from datetime import datetime

import pandas as pd

from config import STAGING_DIR, COMMITTED_DIR, RESULTS_DIR
from pipeline.emission_calc import load_emission_factors, process_dataframe, compute_summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_id(prefix: str) -> str:
    """Generate a unique ID like stg_20260302_153045_a1b2c3."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:6]
    return f"{prefix}_{ts}_{short_uuid}"


def _ensure_dirs():
    """Create staging / committed / results dirs if missing."""
    for d in (STAGING_DIR, COMMITTED_DIR, RESULTS_DIR):
        os.makedirs(d, exist_ok=True)


# ---------------------------------------------------------------------------
# Staging operations
# ---------------------------------------------------------------------------

def save_to_staging(df: pd.DataFrame, year: int, scope: str,
                    filenames: list[str]) -> dict:
    """Save a processed (cleaned + categorised) DataFrame to staging.

    Creates:
      - data/staging/{staging_id}.json   (metadata)
      - data/staging/{staging_id}_data.csv  (row-level data)

    Returns the metadata dict.
    """
    _ensure_dirs()
    staging_id = _generate_id("stg")

    # Category summary for preview
    cat_summary = (
        df.groupby("category")
        .agg(items=("description", "count"), total_kg=("kg", "sum"))
        .sort_values("total_kg", ascending=False)
        .reset_index()
    )
    cat_dict = {
        row["category"]: {"items": int(row["items"]), "total_kg": round(row["total_kg"], 2)}
        for _, row in cat_summary.iterrows()
    }

    uncat = cat_summary[cat_summary["category"] == "Uncategorized"]
    uncat_count = int(uncat["items"].values[0]) if not uncat.empty else 0
    uncat_kg = round(float(uncat["total_kg"].values[0]), 2) if not uncat.empty else 0.0

    metadata = {
        "staging_id": staging_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "year": int(year),
        "scope": scope,
        "filenames": filenames,
        "total_items": len(df),
        "total_kg": round(float(df["kg"].sum()), 2),
        "uncategorized_count": uncat_count,
        "uncategorized_kg": uncat_kg,
        "category_summary": cat_dict,
        "status": "pending",
    }

    # Write metadata JSON
    meta_path = os.path.join(STAGING_DIR, f"{staging_id}.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Write row-level CSV
    csv_path = os.path.join(STAGING_DIR, f"{staging_id}_data.csv")
    df.to_csv(csv_path, index=False)

    return metadata


def load_staging(staging_id: str) -> tuple[dict, pd.DataFrame]:
    """Load a staging record and its DataFrame."""
    meta_path = os.path.join(STAGING_DIR, f"{staging_id}.json")
    csv_path = os.path.join(STAGING_DIR, f"{staging_id}_data.csv")

    with open(meta_path, "r") as f:
        metadata = json.load(f)

    df = pd.read_csv(csv_path)
    return metadata, df


def list_staging() -> list[dict]:
    """Return all pending staging records sorted by created_at desc."""
    _ensure_dirs()
    records = []
    for fname in os.listdir(STAGING_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(STAGING_DIR, fname), "r") as f:
                records.append(json.load(f))
    records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return records


def delete_staging(staging_id: str) -> bool:
    """Delete a staging record (cancel upload)."""
    meta_path = os.path.join(STAGING_DIR, f"{staging_id}.json")
    csv_path = os.path.join(STAGING_DIR, f"{staging_id}_data.csv")
    deleted = False
    for p in (meta_path, csv_path):
        if os.path.exists(p):
            os.remove(p)
            deleted = True
    return deleted


# ---------------------------------------------------------------------------
# Commit operations
# ---------------------------------------------------------------------------

def commit_staging(staging_id: str) -> dict:
    """Commit a staged upload: compute emissions, write to committed/, recompute.

    Returns the committed record metadata.
    """
    _ensure_dirs()
    metadata, df = load_staging(staging_id)

    # Compute emissions
    factors = load_emission_factors()
    category_emissions, summary = process_dataframe(df, factors)

    # Build committed record
    commit_id = _generate_id("cmt")
    committed = {
        **metadata,
        "commit_id": commit_id,
        "committed_at": datetime.now().isoformat(timespec="seconds"),
        "status": "committed",
        "emissions_summary": summary,
    }
    # Replace staging_id key to keep history
    committed.pop("staging_id", None)

    # Write committed JSON
    cmt_meta_path = os.path.join(COMMITTED_DIR, f"{commit_id}.json")
    with open(cmt_meta_path, "w") as f:
        json.dump(committed, f, indent=2)

    # Copy CSV data
    csv_src = os.path.join(STAGING_DIR, f"{staging_id}_data.csv")
    csv_dst = os.path.join(COMMITTED_DIR, f"{commit_id}_data.csv")
    df.to_csv(csv_dst, index=False)

    # Remove staging record
    delete_staging(staging_id)

    # Recompute the global emissions summary
    recompute_emissions()

    return committed


def list_committed() -> list[dict]:
    """Return all committed records sorted by committed_at desc."""
    _ensure_dirs()
    records = []
    for fname in os.listdir(COMMITTED_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(COMMITTED_DIR, fname), "r") as f:
                records.append(json.load(f))
    records.sort(key=lambda r: r.get("committed_at", ""), reverse=True)
    return records


def delete_committed(commit_id: str) -> bool:
    """Delete a committed record and recompute emissions."""
    meta_path = os.path.join(COMMITTED_DIR, f"{commit_id}.json")
    csv_path = os.path.join(COMMITTED_DIR, f"{commit_id}_data.csv")
    deleted = False
    for p in (meta_path, csv_path):
        if os.path.exists(p):
            os.remove(p)
            deleted = True
    if deleted:
        recompute_emissions()
    return deleted


# ---------------------------------------------------------------------------
# Recompute
# ---------------------------------------------------------------------------

def recompute_emissions() -> dict:
    """Rebuild emissions_summary.json from all committed records.

    For years with committed data, recompute from the CSV files.
    For years without committed data, preserve existing values
    (lazy migration for legacy 2023/2024/2025 seeded data).

    Returns the full updated summary dict.
    """
    _ensure_dirs()

    # Load current summary (preserves legacy years)
    summary_path = os.path.join(RESULTS_DIR, "emissions_summary.json")
    try:
        with open(summary_path, "r") as f:
            existing = json.load(f)
    except Exception:
        existing = {}

    # Group committed records by year
    committed_records = list_committed()
    by_year: dict[int, list[dict]] = {}
    for rec in committed_records:
        yr = rec["year"]
        by_year.setdefault(yr, []).append(rec)

    # Track which years have committed data
    years_with_data = set()

    factors = load_emission_factors()

    for year, records in by_year.items():
        years_with_data.add(year)

        # Concatenate all CSVs for this year
        dfs = []
        for rec in records:
            csv_path = os.path.join(COMMITTED_DIR, f"{rec['commit_id']}_data.csv")
            if os.path.exists(csv_path):
                dfs.append(pd.read_csv(csv_path))

        if not dfs:
            continue

        combined = pd.concat(dfs, ignore_index=True)
        _, summary = process_dataframe(combined, factors)

        # Compute % change from baseline
        baseline_carbon = existing.get("2023", {}).get(
            "total_carbon_tCO2e", summary["total_carbon_tCO2e"]
        )
        if baseline_carbon > 0:
            summary["pct_change_from_baseline"] = (
                (summary["total_carbon_tCO2e"] - baseline_carbon) / baseline_carbon
            )
        else:
            summary["pct_change_from_baseline"] = 0

        existing[str(year)] = summary

    # Write updated summary
    with open(summary_path, "w") as f:
        json.dump(existing, f, indent=2)

    return existing
