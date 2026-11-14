"""Tests for read-only Stage 3 source selection and audit records."""

from __future__ import annotations

from src.pass_through.data import build_source_panel, load_stage3_sources, wpi_zero_audit
from src.pass_through.validation import validate_source_inputs


def test_source_selection_and_wpi_zero_audit_match_project_inputs() -> None:
    sources = load_stage3_sources()
    report = validate_source_inputs(sources)

    assert report["expected_months"] == 132
    assert report["sample_start"] == "2014-01-01"
    assert report["sample_end"] == "2024-12-01"
    assert report["cpi_published_missing_in_sample"] == 0
    assert report["sources"]["wpi"]["rows"] == len(sources["wpi"])
    assert sum(report["wpi_zero_summary"]["zero_observations"]) == 505
    assert {item["series"] for item in report["selected_wpi_checks"]} == {
        "All commodities",
        "II FUEL & POWER",
        "III   MANUFACTURED PRODUCTS",
    }
    assert all(
        item["observations"] == 132
        and item["zeros"] == 0
        and item["missing"] == 0
        and item["minimum"] > 0
        for item in report["selected_wpi_checks"]
    )


def test_panel_uses_exact_cpi_and_wpi_series() -> None:
    panel = build_source_panel(load_stage3_sources())

    assert panel["date"].is_monotonic_increasing
    assert panel["date"].is_unique
    assert panel.loc[panel["date"].eq("2014-01-01"), "cpi_series_label"].iloc[0] == "Back"
    assert panel["wpi_all_commodities_index_code"].dropna().unique().tolist() == [1_000_000_000]
    assert panel["wpi_fuel_power_index_code"].dropna().unique().tolist() == [1_200_000_000]
    assert panel["wpi_manufactured_index_code"].dropna().unique().tolist() == [1_300_000_000]


def test_wpi_zero_audit_keeps_exact_rows_without_recode() -> None:
    sources = load_stage3_sources()
    zeros, summary = wpi_zero_audit(sources["wpi"])

    assert len(zeros) == 505
    assert set(zeros["index_value"]) == {0}
    assert len(summary) == 6
    assert set(summary["comm_name"]) == {
        "Cauliflower",
        "Grapes",
        "Litchi",
        "Mango",
        "Orange",
        "Peas (Green)",
    }
