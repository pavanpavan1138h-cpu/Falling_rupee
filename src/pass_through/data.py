"""Read-only loading and alignment of source data for Stage 3."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_ROOT = ROOT / "data" / "processed"
STAGE3_DATA_ROOT = PROCESSED_ROOT / "stage3"

SOURCE_FILES = {
    "cpi": PROCESSED_ROOT / "cpi_monthly_clean.csv",
    "wpi": PROCESSED_ROOT / "wpi_monthly_clean.csv",
    "fx": PROCESSED_ROOT / "usd_inr_monthly_clean.csv",
    "brent": PROCESSED_ROOT / "brent_monthly_clean.csv",
    "repo": PROCESSED_ROOT / "repo_rate_clean.csv",
    "neer_reer": PROCESSED_ROOT / "neer_reer_monthly_clean.csv",
}

WPI_SERIES = {
    "wpi_all_commodities_index": ("All commodities", 1_000_000_000),
    "wpi_fuel_power_index": ("II FUEL & POWER", 1_200_000_000),
    "wpi_manufactured_index": ("III   MANUFACTURED PRODUCTS", 1_300_000_000),
}


def _read_monthly_csv(path: Path, allow_duplicate_dates: bool = False) -> pd.DataFrame:
    """Load a source table and normalize its date column without changing the file."""
    if not path.is_file():
        raise FileNotFoundError(f"Required Stage 3 source file is missing: {path}")
    frame = pd.read_csv(path)
    if "date" not in frame.columns:
        raise ValueError(f"Required date column is missing from {path}.")
    frame["date"] = (
        pd.to_datetime(frame["date"], errors="raise").dt.to_period("M").dt.to_timestamp()
    )
    if frame["date"].duplicated().any() and not allow_duplicate_dates:
        duplicates = frame.loc[frame["date"].duplicated(keep=False), "date"].astype(str).tolist()
        raise ValueError(f"Duplicate monthly dates in {path}: {duplicates[:5]}")
    return frame.sort_values("date").reset_index(drop=True)


def _select_cpi(frame: pd.DataFrame) -> pd.DataFrame:
    """Select the publisher's All India, Combined, CPI General record."""
    required = {"state", "sector", "division", "index_value", "inflation_value"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"CPI source is missing required fields: {sorted(missing)}")
    selected = frame.loc[
        frame["state"].eq("All India")
        & frame["sector"].eq("Combined")
        & frame["division"].eq("CPI (General)"),
        ["date", "index_value", "inflation_value", "series_label", "base_year"],
    ].copy()
    if selected.empty:
        raise ValueError("No All India / Combined / CPI (General) record was found.")
    if selected["date"].duplicated().any():
        raise ValueError("CPI General selection contains multiple records for a month.")
    return selected.rename(
        columns={
            "index_value": "cpi_index",
            "inflation_value": "cpi_published_inflation",
            "series_label": "cpi_series_label",
            "base_year": "cpi_base_year",
        }
    )


def _select_wpi(frame: pd.DataFrame, name: str, code: int, output: str) -> pd.DataFrame:
    """Select one WPI series by both exact publisher name and code."""
    required = {"comm_name", "comm_code", "comm_wt", "index_value"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"WPI source is missing required fields: {sorted(missing)}")
    selected = frame.loc[
        frame["comm_name"].eq(name) & frame["comm_code"].eq(code),
        ["date", "comm_name", "comm_code", "comm_wt", "index_value"],
    ].copy()
    if selected.empty:
        raise ValueError(f"WPI series {name!r} ({code}) was not found.")
    if selected["date"].duplicated().any():
        raise ValueError(f"WPI series {name!r} has duplicate monthly dates.")
    if selected["comm_name"].nunique() != 1 or selected["comm_code"].nunique() != 1:
        raise ValueError(f"WPI series identity is ambiguous for {name!r} ({code}).")
    selected = selected.rename(
        columns={
            "comm_name": f"{output}_name",
            "comm_code": f"{output}_code",
            "comm_wt": f"{output}_weight",
            "index_value": output,
        }
    )
    return selected[["date", output, f"{output}_name", f"{output}_code", f"{output}_weight"]]


def load_stage3_sources(root: Path = ROOT) -> dict[str, pd.DataFrame]:
    """Load the six existing project inputs without writing to or altering them."""
    processed = root / "data" / "processed"
    paths = {
        "cpi": processed / "cpi_monthly_clean.csv",
        "wpi": processed / "wpi_monthly_clean.csv",
        "fx": processed / "usd_inr_monthly_clean.csv",
        "brent": processed / "brent_monthly_clean.csv",
        "repo": processed / "repo_rate_clean.csv",
        "neer_reer": processed / "neer_reer_monthly_clean.csv",
    }
    return {
        name: _read_monthly_csv(path, allow_duplicate_dates=name == "wpi")
        for name, path in paths.items()
    }


def build_source_panel(sources: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Align the verified source series on the exchange-rate monthly calendar."""
    missing_sources = set(SOURCE_FILES).difference(sources)
    if missing_sources:
        raise ValueError(f"Missing Stage 3 source tables: {sorted(missing_sources)}")

    cpi = _select_cpi(sources["cpi"])
    wpi = sources["wpi"].copy()
    selected_wpi = [
        _select_wpi(wpi, name, code, output) for output, (name, code) in WPI_SERIES.items()
    ]
    fx = sources["fx"]
    if "usd_inr_monthly" not in fx.columns:
        raise ValueError("USD/INR source is missing usd_inr_monthly.")
    brent = sources["brent"]
    if "brent_usd_per_barrel" not in brent.columns:
        raise ValueError("Brent source is missing brent_usd_per_barrel.")
    repo = sources["repo"]
    if "repo_rate" not in repo.columns:
        raise ValueError("Repo-rate source is missing repo_rate.")
    neer_reer = sources["neer_reer"]
    required_neer = {"Trade_NEER", "Trade_REER", "Export_NEER", "Export_REER"}
    missing_neer = required_neer.difference(neer_reer.columns)
    if missing_neer:
        raise ValueError(f"NEER/REER source is missing fields: {sorted(missing_neer)}")

    panel = fx[["date", "usd_inr_monthly"]].copy()
    panel = panel.merge(cpi, on="date", how="left", validate="one_to_one")
    for selected in selected_wpi:
        panel = panel.merge(selected, on="date", how="left", validate="one_to_one")
    panel = panel.merge(
        brent[["date", "brent_usd_per_barrel"]], on="date", how="left", validate="one_to_one"
    )
    panel = panel.merge(repo[["date", "repo_rate"]], on="date", how="left", validate="one_to_one")
    panel = panel.merge(
        neer_reer[["date", "Trade_NEER", "Trade_REER", "Export_NEER", "Export_REER"]],
        on="date",
        how="left",
        validate="one_to_one",
    )
    return panel.sort_values("date").reset_index(drop=True)


def wpi_zero_audit(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return exact zero observations and per-series summaries without recoding them."""
    required = {"comm_name", "comm_code", "comm_wt", "date", "index_value"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"WPI source is missing required fields: {sorted(missing)}")
    values = pd.to_numeric(frame["index_value"], errors="coerce")
    zeros = frame.loc[values.eq(0), ["comm_name", "comm_code", "comm_wt", "date", "index_value"]]
    zero_rows = zeros.copy()
    zero_rows["date"] = pd.to_datetime(zero_rows["date"]).dt.to_period("M").dt.to_timestamp()
    summary = (
        zero_rows.groupby(["comm_name", "comm_code", "comm_wt"], as_index=False)
        .agg(
            zero_observations=("date", "size"),
            first_zero=("date", "min"),
            last_zero=("date", "max"),
        )
        .sort_values(["comm_name", "comm_code"])
        .reset_index(drop=True)
    )
    return zero_rows.sort_values(["comm_name", "comm_code", "date"]), summary
