"""Reproducible Stage 2 CPI inflation forecasting entry point."""

from __future__ import annotations

import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.forecasting.inflation.data import (
    ROOT,
    build_fx_forecast_archive,
    load_feature_panel,
    load_published_cpi_target,
)
from src.forecasting.inflation.evaluation import forecast_metrics
from src.forecasting.inflation.features import (
    CONFIGURATIONS,
    HORIZONS,
    build_configuration_frames,
)
from src.forecasting.inflation.forecasting import (
    run_inflation_experiments,
    split_train_validation_test,
)

REPORT_ROOT = ROOT / "reports" / "experiments"
PREDICTION_ROOT = ROOT / "artifacts" / "predictions" / "inflation"
METRIC_ROOT = ROOT / "artifacts" / "metrics" / "inflation"
MODEL_ROOT = ROOT / "artifacts" / "models" / "inflation"
VISUALIZATION_ROOT = ROOT / "visualizations" / "inflation"
SEED = 42


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _protected_file_hashes() -> dict[str, str]:
    directories = (ROOT / "data" / "raw", ROOT / "data" / "processed")
    return {
        str(path.relative_to(ROOT)): _sha256(path)
        for directory in directories
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _stage2_common_frames(
    frames: dict[tuple[str, int], pd.DataFrame],
) -> dict[tuple[str, int], pd.DataFrame]:
    """Restrict every configuration to the exact common origins for each horizon."""
    common_frames: dict[tuple[str, int], pd.DataFrame] = {}
    for horizon in HORIZONS:
        common_origins = frames[("C0", horizon)]["forecast_origin"]
        for configuration in CONFIGURATIONS[1:]:
            common_origins = common_origins[
                common_origins.isin(frames[(configuration, horizon)]["forecast_origin"])
            ]
        if common_origins.empty:
            raise ValueError(f"No common C0-C3 origins for horizon {horizon}.")
        for configuration in CONFIGURATIONS:
            selected = frames[(configuration, horizon)]
            common_frames[(configuration, horizon)] = (
                selected.loc[selected["forecast_origin"].isin(common_origins)]
                .sort_values("forecast_origin")
                .reset_index(drop=True)
            )
    return common_frames


def _training_thresholds(
    frames: dict[tuple[str, int], pd.DataFrame],
    feature_panel: pd.DataFrame,
) -> tuple[dict[int, float], dict[int, float], pd.DataFrame]:
    """Compute diagnostic thresholds only from the initial training portions."""
    inflation_thresholds: dict[int, float] = {}
    brent_thresholds: dict[int, float] = {}
    brent_rows: list[pd.DataFrame] = []
    for horizon in HORIZONS:
        frame = frames[("C0", horizon)]
        train_indices, _, test_indices = split_train_validation_test(frame)
        train = frame.iloc[train_indices]
        validation = frame.iloc[int(len(frame) * 0.70) : int(len(frame) * 0.85)]
        first_validation_origin = validation["forecast_origin"].iloc[0]
        eligible_train = train.loc[train["target_date"] < first_validation_origin]
        inflation_thresholds[horizon] = float(eligible_train["target_cpi_inflation"].quantile(0.90))

        training_target_dates = set(eligible_train["target_date"])
        target_brent = feature_panel.loc[
            feature_panel["date"].isin(training_target_dates),
            ["date", "brent_mom_pct_change"],
        ].dropna()
        brent_thresholds[horizon] = float(target_brent["brent_mom_pct_change"].quantile(0.95))
        test = frame.iloc[test_indices]
        test_dates = test["target_date"]
        diagnostic = feature_panel.loc[
            feature_panel["date"].isin(test_dates),
            ["date", "brent_mom_pct_change"],
        ].rename(columns={"date": "target_date", "brent_mom_pct_change": "diagnostic_value"})
        diagnostic["horizon"] = horizon
        brent_rows.append(diagnostic)
    return inflation_thresholds, brent_thresholds, pd.concat(brent_rows, ignore_index=True)


def _run_lag_sensitivity(
    frames: dict[tuple[str, int], pd.DataFrame],
) -> pd.DataFrame:
    """Compare the C0 autoregression with a parsimonious CPI lag-1/lag-12 variant."""
    from sklearn.linear_model import LinearRegression

    rows: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        frame = frames[("C0", horizon)]
        train_idx, _, test_idx = split_train_validation_test(frame)
        test = frame.iloc[test_idx]
        columns = ["cpi_lag_1", "cpi_lag_12"]
        for _, row in test.iterrows():
            origin = row["forecast_origin"]
            known = frame.loc[(frame["forecast_origin"] < origin) & (frame["target_date"] < origin)]
            model = LinearRegression().fit(
                known[columns],
                known["target_cpi_inflation"],
            )
            predicted = float(model.predict(row[columns].to_frame().T)[0])
            rows.append(
                {
                    "horizon": horizon,
                    "configuration": "C0_lags_1_12",
                    "model": "autoregression_reduced_lags",
                    "forecast_origin": origin,
                    "target_date": row["target_date"],
                    "actual": row["target_cpi_inflation"],
                    "predicted": predicted,
                    "error": predicted - row["target_cpi_inflation"],
                    "training_rows": len(known),
                    "lags": "1,12",
                }
            )
        base = frame.iloc[test_idx]
        actual = base["target_cpi_inflation"].to_numpy(dtype=float)
        baseline_pred = rows[-len(test) :]
        metrics = forecast_metrics(
            actual,
            np.asarray([item["predicted"] for item in baseline_pred]),
        )
        rows.append(
            {
                "horizon": horizon,
                "configuration": "C0_lags_1_12_summary",
                "model": "autoregression_reduced_lags",
                "evaluation_n": len(test),
                **metrics,
                "lags": "1,12",
            }
        )
    return pd.DataFrame(rows)


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _create_visualizations(predictions: pd.DataFrame, comparison: pd.DataFrame) -> list[str]:
    VISUALIZATION_ROOT.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    for horizon in HORIZONS:
        metrics = comparison.loc[
            (comparison["horizon"] == horizon) & (comparison["model"] != "cpi_persistence")
        ]
        pivot = metrics.pivot(index="model", columns="configuration", values="rmse")
        ax = pivot.plot(kind="bar", figsize=(10, 5), rot=20)
        ax.set_title(f"CPI inflation test RMSE by information set ({horizon}-month horizon)")
        ax.set_ylabel("RMSE (percentage points)")
        ax.set_xlabel("Model")
        ax.legend(title="Configuration")
        ax.grid(axis="y", alpha=0.25)
        path = VISUALIZATION_ROOT / f"rmse_comparison_{horizon}m.png"
        ax.figure.tight_layout()
        ax.figure.savefig(path, dpi=160)
        plt.close(ax.figure)
        created.append(str(path.relative_to(ROOT)))

        selected = predictions.loc[
            (predictions["horizon"] == horizon)
            & (
                (
                    (predictions["configuration"] == "C0")
                    & (predictions["model"] == "cpi_persistence")
                )
                | (predictions["model"] == "sarimax")
            )
        ]
        actual = selected.loc[selected["configuration"] == "C0"].drop_duplicates("target_date")
        fig, axis = plt.subplots(figsize=(11, 5))
        axis.plot(
            actual["target_date"], actual["actual"], color="black", label="Actual CPI inflation"
        )
        for configuration in CONFIGURATIONS:
            group = selected.loc[
                (selected["configuration"] == configuration) & (selected["model"] == "sarimax")
            ].sort_values("target_date")
            axis.plot(
                group["target_date"],
                group["predicted"],
                label=f"{configuration} SARIMAX",
                alpha=0.85,
            )
        if horizon == 1:
            persistence = selected.loc[
                (selected["configuration"] == "C0") & (selected["model"] == "cpi_persistence")
            ].sort_values("target_date")
            axis.plot(
                persistence["target_date"],
                persistence["predicted"],
                linestyle="--",
                label="CPI persistence",
            )
        axis.set_title(f"Published CPI inflation forecasts ({horizon}-month horizon)")
        axis.set_ylabel("Year-on-year inflation (%)")
        axis.set_xlabel("Target month")
        axis.legend(ncol=2)
        axis.grid(alpha=0.25)
        fig.tight_layout()
        path = VISUALIZATION_ROOT / f"sarimax_forecasts_{horizon}m.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        created.append(str(path.relative_to(ROOT)))
    return created


def _configuration_report(comparison: pd.DataFrame, incremental: pd.DataFrame) -> str:
    report = [
        "# CPI Configuration Comparison",
        "",
        "Each information set is evaluated on the same held-out target months within a horizon.",
        "Negative `delta_*_vs_C0` values mean the added information reduced forecast error.",
        "This is predictive association, not causal evidence.",
        "",
        "## Model metrics by configuration",
        "",
        comparison.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Paired incremental comparison against C0",
        "",
        incremental.to_markdown(index=False, floatfmt=".4f"),
        "",
        "A comparison is marked unavailable when there are no common targets. No significance",
        "test is asserted from these limited and potentially overlapping forecast errors.",
        "",
    ]
    return "\n".join(report)


def _methodology_report(metadata: dict[str, Any]) -> str:
    return f"""# CPI Inflation Forecasting Methodology

## Research question and target

Does incorporating exchange-rate and imported-cost information improve forecasts of Indian CPI
inflation compared with CPI-history-only models? The target is the **published All India, Combined,
CPI General year-on-year inflation rate** (`inflation_value`), in percentage points. The CPI index
is not substituted or used as a calculated target.

The target used is the longest contiguous published-rate segment,
{metadata["cpi_target"]["selected_segment"]["start"]} through
{metadata["cpi_target"]["selected_segment"]["end"]}
({metadata["cpi_target"]["selected_segment"]["observations"]} observations). A forecast from origin
month t and horizon h targets CPI inflation at month t+h.

## Information sets

- **C0:** CPI published inflation lags 1, 2, 3, 6, and 12 months.
- **C1:** C0 plus lagged Brent monthly USD-per-barrel level and monthly percentage change
  (lags 1, 2, 3, 6, 12).
- **C2:** C0 plus the ARIMA(0,1,1) USD/INR forecast for t+h and its predicted percentage change
  relative to the origin FX level. Actual future FX observations are never substituted. The FX
  archive retains a separate random-walk forecast benchmark.
- **C3:** C0 plus lagged Brent-INR proxy level and percentage change (lags 1, 2, 3, 6, 12).
  This is an approximate imported-cost proxy, not actual landed crude cost or an official
  import-price index.

These are separate nested comparisons; C1, C2, and C3 are not combined.

## Models

Each configuration/horizon uses an autoregressive distributed-lag OLS model, SARIMAX, Elastic Net,
Random Forest, and XGBoost. The CPI persistence baseline forecasts the last published inflation
value available before each origin and is reported under C0. SARIMAX uses order
{metadata["model_metadata"]["C0_1m"]["sarimax_order"]} and seasonal order
{metadata["model_metadata"]["C0_1m"]["sarimax_seasonal_order"]}; CPI seasonal
history is also represented explicitly by its 12-month lag. SARIMAX is refit at each origin and
forecasts recursively through the horizon using only exogenous features dated no later than that
origin. It is not supplied with future realized Brent, FX, or CPI predictors.

Elastic Net scaling is inside the model pipeline. Random Forest and XGBoost use seed
{metadata["seed"]}, single-thread execution, and constrained parameter grids recorded in the
machine-readable metadata.

## Validation and metric protocol

Origin samples are chronologically partitioned approximately 70% training, 15% validation, and 15%
final test. Hyperparameters are tuned only in three expanding folds within the initial training
block; folds purge target labels not available before their validation origin. Models are refit at
each test origin using only outcomes whose target month precedes that origin. Configurations use
common origins and target months within each horizon.

Metrics are MAE, RMSE, test-mean-referenced out-of-sample R-squared, bias
(`prediction - actual`), and MAPE only when every actual is at least 1 percentage point in absolute
value. Negative R-squared is permitted. Forecast errors overlap for 3- and 6-month horizons;
comparisons are descriptive and no Diebold-Mariano test is reported.

## Assumptions and limitations

The data have observation months but no complete historical release timestamp or vintage archive.
The experiment is retrospective and observation-date based, not a genuine real-time backtest. The
published CPI rate is missing throughout calendar 2025; the 2026 segment has only nine observations.
The analysis therefore uses the uninterrupted 2014–2024 published-rate segment and does not bridge
or silently calculate missing inflation values. See `CPI_DATA_AND_FEATURE_AVAILABILITY.md` and
`STAGE1_INDEPENDENT_RESEARCH_AUDIT.md` for source and prior-stage context.
"""


def _availability_report(
    target_metadata: dict[str, Any],
    fx_metadata: dict[str, Any],
    coverage: dict[str, Any],
    metadata: dict[str, Any],
) -> str:
    rows = pd.DataFrame(
        [
            {
                "configuration_horizon": key,
                "origins": value["observations"],
                "origin_start": value["origin_start"],
                "origin_end": value["origin_end"],
                "target_start": value["target_start"],
                "target_end": value["target_end"],
                "predictor_count": value["feature_count"],
            }
            for key, value in coverage.items()
        ]
    )
    return f"""# CPI Data and Feature Availability

## Verified CPI source facts

- Processed source: `data/processed/cpi_monthly_clean.csv`.
- Selected series: All India / Combined / CPI (General).
- Target: published `inflation_value` only; no substitution from `index_value`.
- Source calendar: {target_metadata["source_date_start"]} to
  {target_metadata["source_date_end"]}, {target_metadata["source_rows"]} monthly rows.
- Published values: {target_metadata["published_observations"]}; missing published values:
  {target_metadata["published_missing"]}.
- Continuous published segments:
  `{json.dumps(target_metadata["published_series_segments"])}`.
- Chosen segment: {target_metadata["selected_segment"]["start"]} to
  {target_metadata["selected_segment"]["end"]},
  {target_metadata["selected_segment"]["observations"]} months.
- The 2025 calendar-year gap in published inflation separates the 2024-base back series from the
  2026 current published-rate segment. The latter contains only nine contiguous months, insufficient
  for a separate, comparable train/validation/test experiment. Neither the CPI index nor a
  calculated inflation series is used to bridge the gap.

## Stage 1 FX forecast coverage

The inspected Stage 1 prediction archive contains only its chronological holdout period and does
not cover the Stage 2 historical training and evaluation origins. Stage 1 metadata verifies ARIMA
order (0,1,1) at all three horizons. Stage 2 therefore reuses matching Stage 1 out-of-sample ARIMA
and random-walk predictions where available and constructs the remaining FX archive using fixed
ARIMA(0,1,1) fits through each forecast origin plus a separate random-walk benchmark.

Archive counts: `{json.dumps(fx_metadata, default=str)}`. All archive rows include origin, target
month, horizon, model, predicted FX level, origin level, and provenance. Historical rolling-origin
forecasts are not genuine real-time forecasts.

## Common feature coverage by configuration and horizon

{rows.to_markdown(index=False)}

All configurations were restricted to common origins within a horizon. Feature counts are CPI
history 5 (C0), CPI+Brent 15 (C1), CPI+predicted FX 7 (C2), and CPI+Brent-INR proxy 15 (C3).

## Availability assumptions

No exact historical CPI, Brent, FX, or macro release timestamps/vintages are available. For the
retrospective observation-date experiment, CPI target lags and commodity/proxy features are lagged
at least one month; C2 is an origin-generated future FX forecast. This prevents target-month
realized values from entering predictors but does not prove that the corresponding source
observations were published by the nominal origin timestamp.
"""


def _forecasting_report(results: dict[str, Any], metadata: dict[str, Any]) -> str:
    comparison: pd.DataFrame = results["comparison"]
    incremental: pd.DataFrame = results["incremental"]
    model_rows = comparison.loc[comparison["model"] != "cpi_persistence"]
    best = model_rows.sort_values(["horizon", "rmse"]).groupby("horizon", as_index=False).first()
    c0_models = model_rows.loc[model_rows["configuration"].eq("C0")]
    report = [
        "# CPI Inflation Forecasting Report",
        "",
        "## Observed results",
        "",
        f"Primary target: published All India Combined CPI General year-on-year inflation, "
        f"{metadata['cpi_target']['selected_segment']['start']} to "
        f"{metadata['cpi_target']['selected_segment']['end']}.",
        "This is a retrospective, observation-date-based experiment, not a real-time backtest.",
        "",
        "### C0 model baselines",
        "",
        c0_models.to_markdown(index=False, floatfmt=".4f"),
        "",
        "### Incremental information-set comparison",
        "",
        incremental.to_markdown(index=False, floatfmt=".4f"),
        "",
        "A negative delta MAE/RMSE means the added information improved the corresponding",
        (
            "metric on identical target months. Results are not causal and no significance is "
            "asserted."
        ),
        "",
        "### Lowest-RMSE model/configuration per horizon",
        "",
        best.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Diagnostics and robustness",
        "",
        f"- Test-window split comparisons: {len(results['early_late'])} descriptive rows.",
        (
            f"- High-inflation error rows: {len(results['high_inflation'])}; thresholds are based "
            "on initial training data."
        ),
        (
            f"- Brent spike error rows: {len(results['oil_spikes'])}; target-month Brent is used "
            "only to label ex-post diagnostics, not as a predictor."
        ),
        (
            f"- Residual diagnostic rows: {len(results['residuals'])}. Ljung-Box results are "
            "exploratory because multi-step errors overlap."
        ),
        (
            "- Lag sensitivity compares C0 autoregression using lags 1,2,3,6,12 with a reduced "
            "lag-1/lag-12 specification."
        ),
        (
            "- CPI back-series/current boundary sensitivity: the 2014–2024 continuous "
            "published-rate segment is used. The disjoint 2026 segment has nine points and cannot "
            "support an independent experiment."
        ),
        "",
        "## Convergence and statistical inference",
        "",
        "Elastic Net convergence warning counts are stored by configuration and horizon in run "
        "metadata.",
        (
            "No Diebold-Mariano test was conducted; the finite test samples and overlapping "
            "3/6-month errors"
        ),
        (
            "do not support a reliable inferential comparison. Prediction intervals were not "
            "generated."
        ),
        "",
        "## Reproducibility and preservation",
        "",
        f"- Python {metadata['environment']['python']}; "
        f"pandas {metadata['environment']['pandas']}; "
        f"scikit-learn {metadata['environment']['scikit_learn']}; statsmodels "
        f"{metadata['environment']['statsmodels']}; XGBoost {metadata['environment']['xgboost']}.",
        f"- Fixed seed: {metadata['seed']}.",
        f"- Protected raw/processed data hash check: {metadata['data_integrity']['status']} "
        f"({metadata['data_integrity']['files_checked']} files).",
        "- No raw or verified processed data were written by Stage 2.",
        "",
        "## Limitations and interpretation",
        "",
        (
            "The CPI published inflation rate is discontinuous at the available 2025 base-series "
            "boundary;"
        ),
        (
            "the uninterrupted older segment is used without calculating substitute inflation. "
            "The test"
        ),
        (
            "sample is short, source vintage and publication timestamps are not archived, and the "
            "2026"
        ),
        (
            "published series is too short for separate evaluation. Imported-cost variables are "
            "predictive"
        ),
        (
            "inputs only; no causal conclusions follow. No CPI index target substitution, "
            "synthetic research"
        ),
        "data, Stage 3/4/5 analysis, SHAP, or dashboard work is included.",
        "",
        "## Files",
        "",
        "- Forecast predictions: `CPI_FORECAST_PREDICTIONS.csv`",
        "- Model metrics: `CPI_MODEL_COMPARISON.csv`",
        "- Paired C0 comparison: `CPI_CONFIGURATION_INCREMENTAL_COMPARISON.csv`",
        "- Method: `CPI_FORECASTING_METHODOLOGY.md`",
        "- Data availability: `CPI_DATA_AND_FEATURE_AVAILABILITY.md`",
        "",
        (
            "**Stage 2 readiness:** results are available for researcher review; do not begin "
            "Stage 3 until approved."
        ),
        "",
    ]
    return "\n".join(report)


def run_stage2_experiments() -> dict[str, pd.DataFrame | dict[str, Any]]:
    """Run Stage 2, preserve protected-data hashes, and write all requested artifacts."""
    protected_before = _protected_file_hashes()
    cpi_target, target_metadata = load_published_cpi_target()
    feature_panel = load_feature_panel()
    fx_archive, fx_metadata = build_fx_forecast_archive(cpi_target["date"], feature_panel)
    raw_frames, coverage = build_configuration_frames(cpi_target, feature_panel, fx_archive)
    frames = _stage2_common_frames(raw_frames)
    target_thresholds, brent_thresholds, brent_diagnostics = _training_thresholds(
        frames,
        feature_panel,
    )
    metadata: dict[str, Any] = {
        "stage": "Stage 2 CPI inflation forecasting",
        "research_question": (
            "Does imported-cost information improve CPI inflation forecasts "
            "compared with CPI-history-only models?"
        ),
        "seed": SEED,
        "horizons_months": HORIZONS,
        "cpi_target": target_metadata,
        "fx_forecast_archive": fx_metadata,
        "configuration_definitions": {
            "C0": "published CPI inflation lags only",
            "C1": "C0 plus lagged Brent USD price and monthly change",
            "C2": "C0 plus predicted USD/INR level and predicted change at horizon",
            "C3": "C0 plus lagged Brent-INR approximate imported-cost proxy",
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": version("numpy"),
            "pandas": version("pandas"),
            "scikit_learn": version("scikit-learn"),
            "statsmodels": version("statsmodels"),
            "xgboost": version("xgboost"),
        },
        "no_synthetic_research_data": True,
        "real_time_backtest": False,
    }
    results = run_inflation_experiments(
        frames,
        coverage,
        target_thresholds,
        brent_diagnostics,
        brent_thresholds,
        metadata,
    )
    sensitivity = _run_lag_sensitivity(frames)
    results["lag_sensitivity"] = sensitivity
    metadata = results["metadata"]
    protected_after = _protected_file_hashes()
    integrity = {
        "status": "unchanged" if protected_before == protected_after else "changed",
        "files_checked": len(protected_before),
        "changed_files": [
            name
            for name in sorted(set(protected_before) | set(protected_after))
            if protected_before.get(name) != protected_after.get(name)
        ],
    }
    if integrity["status"] != "unchanged":
        raise RuntimeError(f"Stage 2 modified protected data: {integrity['changed_files']}")
    metadata["data_integrity"] = integrity

    for directory in (REPORT_ROOT, PREDICTION_ROOT, METRIC_ROOT, MODEL_ROOT, VISUALIZATION_ROOT):
        directory.mkdir(parents=True, exist_ok=True)

    output_frames = {
        "CPI_FORECAST_PREDICTIONS.csv": results["predictions"],
        "CPI_MODEL_COMPARISON.csv": results["comparison"],
        "CPI_CONFIGURATION_INCREMENTAL_COMPARISON.csv": results["incremental"],
        "CPI_RESIDUAL_DIAGNOSTICS.csv": results["residuals"],
        "CPI_HIGH_INFLATION_EPISODES.csv": results["high_inflation"],
        "CPI_BRENT_SPIKE_ERROR_SUMMARY.csv": results["oil_spikes"],
        "CPI_CHRONOLOGICAL_WINDOW_COMPARISON.csv": results["early_late"],
        "CPI_LAG_SENSITIVITY.csv": sensitivity,
        "CPI_FX_FORECAST_ARCHIVE.csv": fx_archive,
    }
    for filename, frame in output_frames.items():
        _write_csv(frame, REPORT_ROOT / filename)
    _write_csv(results["predictions"], PREDICTION_ROOT / "stage2_cpi_predictions.csv")
    _write_csv(results["comparison"], METRIC_ROOT / "stage2_cpi_model_comparison.csv")
    _write_csv(results["incremental"], METRIC_ROOT / "stage2_cpi_incremental_comparison.csv")
    with (METRIC_ROOT / "stage2_cpi_run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, default=str)
    with (MODEL_ROOT / "stage2_model_configurations.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata["model_metadata"], handle, indent=2, default=str)
    metadata["visualizations"] = _create_visualizations(
        results["predictions"],
        results["comparison"],
    )
    # Persist the metadata again after visualization paths have been recorded.
    with (METRIC_ROOT / "stage2_cpi_run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, default=str)

    method_text = _methodology_report(metadata)
    availability_text = _availability_report(
        target_metadata,
        fx_metadata,
        coverage,
        metadata,
    )
    (REPORT_ROOT / "CPI_FORECASTING_METHODOLOGY.md").write_text(
        method_text,
        encoding="utf-8",
    )
    (REPORT_ROOT / "CPI_DATA_AND_FEATURE_AVAILABILITY.md").write_text(
        availability_text,
        encoding="utf-8",
    )
    (REPORT_ROOT / "CPI_CONFIGURATION_COMPARISON.md").write_text(
        _configuration_report(results["comparison"], results["incremental"]),
        encoding="utf-8",
    )
    (REPORT_ROOT / "CPI_INFLATION_FORECASTING_REPORT.md").write_text(
        _forecasting_report(results, metadata),
        encoding="utf-8",
    )
    return results


def main() -> None:
    results = run_stage2_experiments()
    print(
        f"Stage 2 complete: {len(results['predictions'])} forecast records; "
        f"{len(results['comparison'])} model/configuration/horizon metric rows."
    )
    print(results["comparison"].to_string(index=False))


if __name__ == "__main__":
    main()
