"""Input integrity and Stage 3 sample validation."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.pass_through.data import WPI_SERIES, wpi_zero_audit
from src.pass_through.features import SAMPLE_END, SAMPLE_START


def _monthly_gaps(frame: pd.DataFrame) -> list[str]:
    """Return missing calendar months between a source series' endpoints."""
    dates = pd.to_datetime(frame["date"]).dt.to_period("M")
    observed = set(dates)
    expected = pd.period_range(dates.min(), dates.max(), freq="M")
    return [str(period) for period in expected if period not in observed]


def validate_source_inputs(sources: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Validate identities, calendars, values, and WPI zero semantics without edits."""
    required = {"cpi", "wpi", "fx", "brent", "repo", "neer_reer"}
    missing = required.difference(sources)
    if missing:
        raise ValueError(f"Missing source tables for Stage 3 validation: {sorted(missing)}")
    source_summary: dict[str, Any] = {}
    for name in sorted(required):
        frame = sources[name]
        if "date" not in frame:
            raise ValueError(f"{name} source does not contain a date column.")
        if frame["date"].isna().any():
            raise ValueError(f"{name} source contains missing dates.")
        if frame["date"].duplicated().any() and name != "wpi":
            raise ValueError(f"{name} source contains duplicate dates.")
        source_summary[name] = {
            "rows": int(len(frame)),
            "start": pd.to_datetime(frame["date"]).min().date().isoformat(),
            "end": pd.to_datetime(frame["date"]).max().date().isoformat(),
            "duplicate_dates": int(frame["date"].duplicated().sum()),
            "missing_calendar_months": _monthly_gaps(frame) if name != "wpi" else [],
        }
    if source_summary["cpi"]["missing_calendar_months"]:
        raise ValueError("CPI source has missing calendar months; no interpolation is permitted.")

    wpi_frame = sources["wpi"]
    zero_rows, zero_summary = wpi_zero_audit(wpi_frame)
    wpi_zero_report = zero_summary.copy()
    selected_checks: list[dict[str, Any]] = []
    for name, code in WPI_SERIES.values():
        selected = wpi_frame.loc[
            wpi_frame["comm_name"].eq(name)
            & wpi_frame["comm_code"].eq(code)
            & pd.to_datetime(wpi_frame["date"]).between(SAMPLE_START, SAMPLE_END)
        ].copy()
        values = pd.to_numeric(selected["index_value"], errors="coerce")
        if selected.empty:
            raise ValueError(f"Selected WPI series {name!r} is absent from the common sample.")
        expected = pd.period_range(SAMPLE_START.to_period("M"), SAMPLE_END.to_period("M"), freq="M")
        observed = pd.to_datetime(selected["date"]).dt.to_period("M")
        if len(selected) != len(expected) or not observed.reset_index(drop=True).equals(
            pd.Series(expected)
        ):
            raise ValueError(
                f"Selected WPI series {name!r} is not continuous in the common sample."
            )
        selected_checks.append(
            {
                "series": name,
                "code": int(code),
                "weight": float(selected["comm_wt"].iloc[0]),
                "observations": int(len(selected)),
                "missing": int(values.isna().sum()),
                "zeros": int(values.eq(0).sum()),
                "nonpositive": int(values.le(0).sum()),
                "minimum": float(values.min()),
                "maximum": float(values.max()),
            }
        )
        if values.isna().any() or values.le(0).any():
            raise ValueError(f"Selected WPI series {name!r} is not positive and complete.")

    zero_dates = zero_rows.copy()
    zero_dates["date"] = pd.to_datetime(zero_dates["date"]).dt.strftime("%Y-%m-%d")
    return {
        "sample_start": SAMPLE_START.date().isoformat(),
        "sample_end": SAMPLE_END.date().isoformat(),
        "expected_months": int(len(pd.period_range(SAMPLE_START, SAMPLE_END, freq="M"))),
        "sources": source_summary,
        "wpi_zero_summary": wpi_zero_report,
        "wpi_zero_dates": zero_dates,
        "selected_wpi_checks": selected_checks,
        "cpi_published_missing_in_sample": int(
            pd.to_numeric(
                sources["cpi"].loc[
                    pd.to_datetime(sources["cpi"]["date"]).between(SAMPLE_START, SAMPLE_END),
                    "inflation_value",
                ],
                errors="coerce",
            )
            .isna()
            .sum()
        ),
    }


def validate_stage3_panel(panel: pd.DataFrame) -> dict[str, Any]:
    """Check transformed sample coverage and finite-value requirements."""
    expected = pd.period_range(SAMPLE_START, SAMPLE_END, freq="M")
    periods = pd.to_datetime(panel["date"]).dt.to_period("M")
    if periods.duplicated().any() or not periods.reset_index(drop=True).equals(pd.Series(expected)):
        raise ValueError("The transformed Stage 3 sample must have exactly 132 ordered months.")
    required = [
        "fx_log_change_pct",
        "cpi_annual_log_inflation",
        "wpi_all_commodities_annual_log_inflation",
        "wpi_fuel_power_annual_log_inflation",
        "wpi_manufactured_annual_log_inflation",
    ]
    availability: dict[str, Any] = {}
    for column in required:
        values = pd.to_numeric(panel[column], errors="coerce")
        if np.isinf(values.to_numpy(dtype=float)).any():
            raise ValueError(f"Non-finite values found in required feature {column}.")
        availability[column] = {
            "nonmissing": int(values.notna().sum()),
            "missing": int(values.isna().sum()),
        }
    return {
        "rows": int(len(panel)),
        "start": pd.to_datetime(panel["date"]).min().date().isoformat(),
        "end": pd.to_datetime(panel["date"]).max().date().isoformat(),
        "availability": availability,
    }
