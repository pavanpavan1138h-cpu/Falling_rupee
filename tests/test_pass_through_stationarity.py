"""Unit tests for conservative integration classifications."""

from __future__ import annotations

import pandas as pd

from src.pass_through.stationarity import classify_integration


def test_integration_classification_requires_adf_and_kpss_agreement() -> None:
    results = pd.DataFrame(
        [
            {"series": "stationary", "difference_order": 0, "adf_pvalue": 0.01, "kpss_pvalue": 0.1},
            {"series": "ambiguous", "difference_order": 0, "adf_pvalue": 0.01, "kpss_pvalue": 0.01},
            {"series": "ambiguous", "difference_order": 1, "adf_pvalue": 0.1, "kpss_pvalue": 0.01},
            {
                "series": "possible_i2",
                "difference_order": 0,
                "adf_pvalue": 0.8,
                "kpss_pvalue": 0.01,
            },
            {
                "series": "possible_i2",
                "difference_order": 1,
                "adf_pvalue": 0.8,
                "kpss_pvalue": 0.01,
            },
            {
                "series": "possible_i2",
                "difference_order": 2,
                "adf_pvalue": 0.01,
                "kpss_pvalue": 0.1,
            },
        ]
    )

    classified = classify_integration(results).set_index("series")

    assert classified.loc["stationary", "classification"] == "I(0)-consistent"
    assert classified.loc["ambiguous", "classification"] == "ambiguous / tests disagree"
    assert classified.loc["possible_i2", "classification"] == "possible I(2); verify"
