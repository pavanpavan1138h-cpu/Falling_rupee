"""Run the reproducible Stage 4 early-warning classification experiment."""

from __future__ import annotations

import hashlib
import json
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.risk_classification.evaluation import (
    choose_f1_threshold,
    classification_metrics,
)
from src.risk_classification.features import (
    DATA_ROOT,
    FEATURE_COLUMNS,
    HORIZONS,
    ROOT,
    build_classification_frames,
    load_stage4_sources,
)
from src.risk_classification.models import (
    Candidate,
    candidate_grid,
    fit_candidate,
    predict_candidate,
    validation_frame,
)

SEED = 42
DATA_OUTPUT = DATA_ROOT / "stage4"
MODEL_OUTPUT = ROOT / "artifacts" / "models" / "early_warning"
PREDICTION_OUTPUT = ROOT / "artifacts" / "predictions" / "early_warning"
METRIC_OUTPUT = ROOT / "artifacts" / "metrics" / "early_warning"
VISUALIZATION_OUTPUT = ROOT / "visualizations" / "early_warning"
REPORT_OUTPUT = ROOT / "reports" / "experiments"
CONFIGURATIONS = tuple(FEATURE_COLUMNS)
TEST_START = pd.Timestamp("2023-07-01")
TEST_END = pd.Timestamp("2024-12-01")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _protected_hashes() -> dict[str, str]:
    """Hash source data and all pre-Stage-4 project files that must remain unchanged."""
    roots = (
        ROOT / "data" / "raw",
        ROOT / "data" / "processed",
        ROOT / "artifacts",
        ROOT / "visualizations",
        ROOT / "src" / "features",
        ROOT / "src" / "forecasting",
        ROOT / "tests",
        ROOT / "reports",
    )
    excluded = {
        DATA_OUTPUT.resolve(),
        MODEL_OUTPUT.resolve(),
        PREDICTION_OUTPUT.resolve(),
        METRIC_OUTPUT.resolve(),
        VISUALIZATION_OUTPUT.resolve(),
    }
    protected: dict[str, str] = {}
    for base in roots:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or any(
                excluded_path == path.resolve() or excluded_path in path.resolve().parents
                for excluded_path in excluded
            ):
                continue
            if path.name.startswith("STAGE4_") and path.parent == REPORT_OUTPUT:
                continue
            if path.name == "test_early_warning_classification.py":
                continue
            if path.name in {"ISSUE_LOG.md", "RESEARCH_DECISION_LOG.md"}:
                continue
            protected[str(path.relative_to(ROOT))] = _sha256(path)
    return protected


def _package_version(package: str) -> str:
    try:
        return version(package)
    except PackageNotFoundError:
        return "not installed"


def _candidate_metrics(
    candidate: Candidate,
    predictions: pd.DataFrame,
) -> tuple[dict[str, Any], float]:
    threshold = choose_f1_threshold(
        predictions["actual"].to_numpy(dtype=int),
        predictions["probability"].to_numpy(dtype=float),
    )
    result = classification_metrics(
        predictions["actual"].to_numpy(dtype=int),
        predictions["probability"].to_numpy(dtype=float),
        threshold,
        horizon=int(predictions["horizon_months"].iloc[0]),
        target_months=predictions["target_month"],
    )
    result["validation_pr_auc_average_precision"] = float(
        average_precision_score(
            predictions["actual"].to_numpy(dtype=int),
            predictions["probability"].to_numpy(dtype=float),
        )
    )
    result["validation_threshold"] = threshold
    result["candidate_id"] = candidate.candidate_id
    return result, threshold


def _split_counts(frame: pd.DataFrame, horizon: int) -> list[dict[str, Any]]:
    validation_start = pd.Timestamp("2021-01-01") + pd.DateOffset(months=horizon)
    first_test_origin = frame.loc[frame["target_month"].ge(TEST_START), "forecast_origin"].min()
    training = frame.loc[frame["target_month"].le(pd.Timestamp("2020-12-01"))]
    validation = frame.loc[
        frame["target_month"].between(validation_start, pd.Timestamp("2022-12-01"))
    ]
    gap_end = TEST_START - pd.DateOffset(months=1)
    gap = frame.loc[
        frame["target_month"].between(pd.Timestamp("2023-01-01"), gap_end)
    ]
    test = frame.loc[frame["target_month"].between(TEST_START, TEST_END)]
    return [
        {
            "horizon_months": horizon,
            "partition": "initial_training",
            "n": len(training),
            "elevated": int(training["elevated_target"].sum()),
            "non_elevated": int((training["elevated_target"] == 0).sum()),
            "target_start": training["target_month"].min().date().isoformat(),
            "target_end": training["target_month"].max().date().isoformat(),
            "training_label_cutoff": "target month <= 2020-12",
        },
        {
            "horizon_months": horizon,
            "partition": "expanding_validation",
            "n": len(validation),
            "elevated": int(validation["elevated_target"].sum()),
            "non_elevated": int((validation["elevated_target"] == 0).sum()),
            "target_start": validation["target_month"].min().date().isoformat(),
            "target_end": validation["target_month"].max().date().isoformat(),
            "training_label_cutoff": "target month strictly before each validation origin",
        },
        {
            "horizon_months": horizon,
            "partition": "validation_test_gap",
            "n": len(gap),
            "elevated": int(gap["elevated_target"].sum()),
            "non_elevated": int((gap["elevated_target"] == 0).sum()),
            "target_start": gap["target_month"].min().date().isoformat(),
            "target_end": gap["target_month"].max().date().isoformat(),
            "training_label_cutoff": "not scored for model selection or final testing",
        },
        {
            "horizon_months": horizon,
            "partition": "untouched_final_test",
            "n": len(test),
            "elevated": int(test["elevated_target"].sum()),
            "non_elevated": int((test["elevated_target"] == 0).sum()),
            "target_start": test["target_month"].min().date().isoformat(),
            "target_end": test["target_month"].max().date().isoformat(),
            "training_label_cutoff": f"target month strictly before {first_test_origin:%Y-%m}",
        },
    ]


def _markdown_table(frame: pd.DataFrame, columns: list[str] | None = None) -> str:
    selected = frame[columns] if columns else frame
    return selected.to_markdown(index=False, floatfmt=".3f")


def _calibration_bins(
    test_predictions: pd.DataFrame,
    selection: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize observed rates against predicted-risk bins for validation-selected models."""
    rows: list[dict[str, Any]] = []
    bin_edges = np.linspace(0.0, 1.0, 5)
    for horizon in HORIZONS:
        chosen = selection.loc[
            selection["horizon_months"].eq(horizon)
            & selection["overall_horizon_selected"]
        ].iloc[0]
        selected = test_predictions.loc[
            test_predictions["horizon_months"].eq(horizon)
            & test_predictions["configuration"].eq(chosen["configuration"])
            & test_predictions["model"].eq(chosen["model"])
        ].copy()
        selected["probability_bin"] = pd.cut(
            selected["predicted_probability"],
            bins=bin_edges,
            include_lowest=True,
            right=True,
        )
        for bin_index, interval in enumerate(
            selected["probability_bin"].cat.categories, start=1
        ):
            in_bin = selected.loc[selected["probability_bin"].eq(interval)]
            rows.append(
                {
                    "horizon_months": horizon,
                    "configuration": chosen["configuration"],
                    "model": chosen["model"],
                    "bin_number": bin_index,
                    "probability_interval": str(interval),
                    "n": len(in_bin),
                    "mean_predicted_probability": (
                        float(in_bin["predicted_probability"].mean())
                        if len(in_bin)
                        else np.nan
                    ),
                    "observed_elevated_rate": (
                        float(in_bin["actual_inflation_class"].mean())
                        if len(in_bin)
                        else np.nan
                    ),
                    "elevated_count": int(in_bin["actual_inflation_class"].sum()),
                    "interpretation": "descriptive; sparse test bins are unstable",
                }
            )
    return pd.DataFrame(rows)


def _feature_eligibility_table() -> pd.DataFrame:
    """Describe each implemented predictor, its timing, and its model role."""
    descriptions = {
        "cpi_lag_1": (
            "CPI history", "Published inflation at t-1", "Recent inflation persistence"
        ),
        "cpi_lag_3": (
            "CPI history", "Published inflation at t-3", "Short-run inflation persistence"
        ),
        "cpi_lag_6": (
            "CPI history", "Published inflation at t-6", "Medium-run inflation persistence"
        ),
        "cpi_lag_12": (
            "CPI history", "Published inflation at t-12", "Annual inflation persistence"
        ),
        "cpi_change_1m": (
            "CPI history", "CPI(t-1) - CPI(t-2)", "Recent inflation acceleration"
        ),
        "cpi_mean_3m": (
            "CPI history", "Mean CPI inflation over t-3..t-1", "Smoothed recent inflation"
        ),
        "cpi_volatility_6m": (
            "CPI history", "Sample SD of CPI inflation over t-6..t-1",
            "Recent inflation instability"
        ),
        "fx_log_return_1m": (
            "Exchange rate", "100 * log(USD/INR[t-1] / USD/INR[t-2])",
            "Recent rupee depreciation or appreciation"
        ),
        "fx_cumulative_return_3m": (
            "Exchange rate", "Sum of FX log returns over t-3..t-1",
            "Accumulated recent rupee movement"
        ),
        "fx_volatility_6m": (
            "Exchange rate", "Sample SD of FX log returns over t-6..t-1",
            "Recent exchange-rate instability"
        ),
        "brent_log_return_1m": (
            "Imported cost", "100 * log(Brent USD[t-1] / Brent USD[t-2])",
            "Recent global oil-price movement"
        ),
        "brent_cumulative_return_3m": (
            "Imported cost", "Sum of Brent USD log returns over t-3..t-1",
            "Accumulated global oil-price movement"
        ),
        "brent_inr_proxy_log_return_1m": (
            "Imported cost proxy",
            "100 * log((USD/INR * Brent USD)[t-1] / (USD/INR * Brent USD)[t-2])",
            "Joint exchange-rate and Brent price movement"
        ),
        "brent_inr_proxy_cumulative_return_3m": (
            "Imported cost proxy",
            "Sum of Brent-INR product-proxy log returns over t-3..t-1",
            "Accumulated joint exchange-rate and Brent movement"
        ),
    }
    configurations = {
        feature: [
            configuration
            for configuration, feature_list in FEATURE_COLUMNS.items()
            if feature in feature_list
        ]
        for feature_list in FEATURE_COLUMNS.values()
        for feature in feature_list
    }
    rows = []
    unique_features = dict.fromkeys(
        feature for feature_list in FEATURE_COLUMNS.values() for feature in feature_list
    )
    for feature in unique_features:
        family, formula, rationale = descriptions[feature]
        rows.append(
            {
                "feature": feature,
                "family": family,
                "formula_or_construction": formula,
                "economic_justification": rationale,
                "required_lag": "All source observations end at t-1; the target is t+h.",
                "availability_at_origin": (
                    "Reference month precedes origin; actual release/vintage timing is unverified."
                ),
                "leakage_risk": (
                    "Potential real-time availability lag; future realized observations "
                    "are excluded."
                ),
                "model_role": (
                    "C0 CPI-only baseline"
                    if feature.startswith("cpi_")
                    else "Extended configuration"
                ),
                "configurations": ", ".join(configurations[feature]),
                "proxy_limitation": (
                    "Mechanical Brent-USD x USD/INR proxy; not actual landed import cost."
                    if feature.startswith("brent_inr_proxy_")
                    else "Not applicable"
                ),
            }
        )
    return pd.DataFrame(rows)


def _origin_split_manifest(
    frame: pd.DataFrame,
    horizon: int,
) -> pd.DataFrame:
    """Return one row per origin with its partition and known-label training boundary."""
    validation_start = pd.Timestamp("2021-01-01") + pd.DateOffset(months=horizon)
    test = frame.loc[frame["target_month"].between(TEST_START, TEST_END)]
    if test.empty:
        raise ValueError(f"No final-test target observations at horizon {horizon}.")
    first_test_origin = test["forecast_origin"].min()
    rows: list[dict[str, Any]] = []
    for row in frame.itertuples(index=False):
        if row.target_month <= pd.Timestamp("2020-12-01"):
            partition = "initial_training"
            cutoff = pd.NaT
        elif row.target_month < validation_start:
            partition = "validation_warmup"
            cutoff = pd.NaT
        elif row.target_month <= pd.Timestamp("2022-12-01"):
            partition = "expanding_validation"
            cutoff = row.forecast_origin
        elif row.target_month < TEST_START:
            partition = "validation_test_gap"
            cutoff = pd.NaT
        elif row.target_month <= TEST_END:
            partition = "untouched_final_test"
            cutoff = first_test_origin
        else:
            partition = "outside_evaluation_window"
            cutoff = pd.NaT
        mature = (
            frame.loc[frame["target_month"] < cutoff]
            if pd.notna(cutoff)
            else frame.iloc[0:0]
        )
        rows.append(
            {
                "horizon_months": horizon,
                "forecast_origin": row.forecast_origin,
                "target_month": row.target_month,
                "target_inflation": row.target_inflation,
                "elevated_target": int(row.elevated_target),
                "partition": partition,
                "training_label_cutoff_exclusive": cutoff,
                "mature_training_n": len(mature),
                "mature_training_elevated": int(mature["elevated_target"].sum()),
            }
        )
    return pd.DataFrame(rows)


def _write_visualizations(
    target: pd.DataFrame,
    predictions: pd.DataFrame,
    test_metrics: pd.DataFrame,
    selection: pd.DataFrame,
    importance: pd.DataFrame,
    calibration: pd.DataFrame,
) -> None:
    """Save diagnostic plots from observed outcomes and the generated archive."""
    target_series = target["target_inflation"].copy()
    target_series.index = target_series.index.to_timestamp()
    figure, axis = plt.subplots(figsize=(11, 5), constrained_layout=True)
    axis.bar(["Non-elevated (<=6%)", "Elevated (>6%)"],
             [(target_series <= 6.0).sum(), (target_series > 6.0).sum()],
             color=["tab:blue", "tab:orange"])
    axis.set_ylabel("Published CPI months")
    axis.set_title("Observed CPI class distribution, Jan 2014-Dec 2024")
    figure.savefig(VISUALIZATION_OUTPUT / "stage4_class_distribution.png", dpi=150)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(12, 5), constrained_layout=True)
    axis.plot(target_series.index, target_series, color="tab:blue", label="Published CPI inflation")
    axis.axhline(6.0, color="tab:red", linestyle="--", label="Strict >6% threshold")
    elevated = target_series > 6.0
    axis.scatter(target_series.index[elevated], target_series[elevated],
                 color="tab:orange", label="Elevated month", zorder=3)
    axis.set_ylabel("Year-on-year inflation (%)")
    axis.set_title("Observed elevated-inflation episodes")
    axis.legend()
    figure.savefig(VISUALIZATION_OUTPUT / "stage4_inflation_episodes.png", dpi=150)
    plt.close(figure)

    test_predictions = predictions.loc[predictions["partition"].eq("untouched_final_test")]
    for metric_name, curve_name, filename in (
        ("precision_recall", "Precision-recall", "stage4_test_pr_curves.png"),
        ("roc", "ROC", "stage4_test_roc_curves.png"),
    ):
        figure, axes = plt.subplots(1, len(HORIZONS), figsize=(17, 5), constrained_layout=True)
        for axis, horizon in zip(axes, HORIZONS, strict=True):
            subset = test_predictions.loc[test_predictions["horizon_months"].eq(horizon)]
            for (configuration, model), group in subset.groupby(["configuration", "model"]):
                actual = group["actual_inflation_class"].to_numpy(dtype=int)
                probability = group["predicted_probability"].to_numpy(dtype=float)
                if len(np.unique(actual)) < 2:
                    continue
                label = f"{configuration}/{model}"
                if metric_name == "precision_recall":
                    from sklearn.metrics import precision_recall_curve

                    x_values, y_values, _ = precision_recall_curve(actual, probability)
                    axis.plot(y_values, x_values, label=label)
                    axis.set_xlabel("Recall")
                    axis.set_ylabel("Precision")
                else:
                    from sklearn.metrics import roc_curve

                    x_values, y_values, _ = roc_curve(actual, probability)
                    axis.plot(x_values, y_values, label=label)
                    axis.plot([0, 1], [0, 1], color="black", linestyle=":")
                    axis.set_xlabel("False-positive rate")
                    axis.set_ylabel("True-positive rate")
            axis.set_title(f"{horizon}-month horizon")
            axis.legend(fontsize="x-small", ncol=2)
        figure.suptitle(f"{curve_name} curves: untouched final test")
        figure.savefig(VISUALIZATION_OUTPUT / filename, dpi=150)
        plt.close(figure)

    figure, axes = plt.subplots(1, len(HORIZONS), figsize=(12, 4), constrained_layout=True)
    for axis, horizon in zip(axes, HORIZONS, strict=True):
        chosen = selection.loc[
            selection["horizon_months"].eq(horizon) & selection["overall_horizon_selected"]
        ].iloc[0]
        group = test_predictions.loc[
            test_predictions["horizon_months"].eq(horizon)
            & test_predictions["configuration"].eq(chosen["configuration"])
            & test_predictions["model"].eq(chosen["model"])
        ]
        actual = group["actual_inflation_class"].to_numpy(dtype=int)
        alerts = group["predicted_alert"].to_numpy(dtype=int)
        matrix = np.array(
            [[((actual == 0) & (alerts == 0)).sum(), ((actual == 0) & (alerts == 1)).sum()],
             [((actual == 1) & (alerts == 0)).sum(), ((actual == 1) & (alerts == 1)).sum()]]
        )
        axis.imshow(matrix, cmap="Blues")
        for (row, column), value in np.ndenumerate(matrix):
            axis.text(column, row, str(value), ha="center", va="center")
        axis.set_xticks([0, 1], ["No alert", "Alert"])
        axis.set_yticks([0, 1], ["Not elevated", "Elevated"])
        axis.set_title(f"{horizon}m: {chosen['configuration']}/{chosen['model']}")
    figure.suptitle("Selected-model final-test confusion matrices")
    figure.savefig(VISUALIZATION_OUTPUT / "stage4_confusion_matrices.png", dpi=150)
    plt.close(figure)

    figure, axes = plt.subplots(1, len(HORIZONS), figsize=(12, 4), constrained_layout=True)
    for axis, horizon in zip(axes, HORIZONS, strict=True):
        group = calibration.loc[calibration["horizon_months"].eq(horizon)]
        valid = group.dropna(subset=["mean_predicted_probability", "observed_elevated_rate"])
        axis.plot([0, 1], [0, 1], color="black", linestyle=":")
        axis.plot(
            valid["mean_predicted_probability"],
            valid["observed_elevated_rate"],
            marker="o",
        )
        axis.set_xlim(0, 1)
        axis.set_ylim(0, 1)
        axis.set_title(f"{horizon}m: selected model")
        axis.set_xlabel("Mean predicted risk")
        axis.set_ylabel("Observed elevated rate")
    figure.suptitle("Final-test calibration (sparse bins; descriptive only)")
    figure.savefig(VISUALIZATION_OUTPUT / "stage4_calibration.png", dpi=150)
    plt.close(figure)

    figure, axes = plt.subplots(1, len(HORIZONS), figsize=(15, 5), constrained_layout=True)
    for axis, horizon in zip(axes, HORIZONS, strict=True):
        chosen = selection.loc[
            selection["horizon_months"].eq(horizon) & selection["overall_horizon_selected"]
        ].iloc[0]
        group = importance.loc[
            importance["horizon_months"].eq(horizon)
            & importance["configuration"].eq(chosen["configuration"])
            & importance["model"].eq(chosen["model"])
        ].copy()
        group["magnitude"] = group["importance"].abs()
        group = group.nlargest(10, "magnitude").sort_values("magnitude")
        axis.barh(group["feature"], group["importance"])
        axis.set_title(f"{horizon}m: {chosen['configuration']}/{chosen['model']}")
    figure.suptitle("Selected-model feature importance (descriptive, not causal)")
    figure.savefig(VISUALIZATION_OUTPUT / "stage4_feature_importance.png", dpi=150)
    plt.close(figure)

    for metric, filename, title in (
        ("pr_auc_average_precision", "stage4_configuration_pr_auc.png", "Average precision"),
        ("brier_score", "stage4_configuration_brier.png", "Brier score"),
    ):
        figure, axes = plt.subplots(1, len(HORIZONS), figsize=(13, 4), constrained_layout=True)
        for axis, horizon in zip(axes, HORIZONS, strict=True):
            group = test_metrics.loc[test_metrics["horizon_months"].eq(horizon)]
            for model, model_group in group.groupby("model"):
                axis.plot(
                    model_group.set_index("configuration").reindex(FEATURE_COLUMNS).index,
                    model_group.set_index("configuration").reindex(FEATURE_COLUMNS)[metric],
                    marker="o",
                    label=model,
                )
            axis.set_title(f"{horizon}-month horizon")
            axis.set_xlabel("Feature configuration")
            axis.set_ylabel(title)
            axis.legend(fontsize="small")
        figure.suptitle(f"Final-test {title} by configuration")
        figure.savefig(VISUALIZATION_OUTPUT / filename, dpi=150)
        plt.close(figure)

    figure, axes = plt.subplots(3, 1, figsize=(12, 10), constrained_layout=True)
    for axis, horizon in zip(axes, HORIZONS, strict=True):
        chosen = selection.loc[
            selection["horizon_months"].eq(horizon)
            & selection["overall_horizon_selected"]
        ].iloc[0]
        selected_predictions = test_predictions.loc[
            test_predictions["horizon_months"].eq(horizon)
            & test_predictions["configuration"].eq(chosen["configuration"])
            & test_predictions["model"].eq(chosen["model"])
        ].sort_values("target_month")
        axis.plot(
            selected_predictions["target_month"],
            selected_predictions["predicted_probability"],
            marker="o",
            label=f"{chosen['configuration']} / {chosen['model']} risk",
        )
        axis.scatter(
            selected_predictions["target_month"],
            selected_predictions["actual_inflation_class"],
            marker="x",
            color="black",
            label="Observed elevated class",
        )
        axis.axhline(chosen["selected_threshold"], color="tab:red", linestyle="--")
        axis.set_ylim(-0.05, 1.05)
        axis.set_ylabel(f"{horizon}-month")
        axis.legend(loc="upper left")
    axes[-1].set_xlabel("CPI target month")
    figure.suptitle("Stage 4 selected validation models: final-test risks")
    figure.savefig(VISUALIZATION_OUTPUT / "stage4_final_test_risk.png", dpi=150)
    plt.close(figure)


def _write_reports(
    source_metadata: dict[str, Any],
    coverage: dict[str, Any],
    split_counts: pd.DataFrame,
    validation_selection: pd.DataFrame,
    test_metrics: pd.DataFrame,
    incremental: pd.DataFrame,
    protected_before: dict[str, str],
    feature_importance: pd.DataFrame,
    calibration: pd.DataFrame,
) -> None:
    """Write Stage 4 reports using observed inputs and outputs only."""
    source_rows = pd.DataFrame(
        [
            {"Source": "Published CPI", "File": source_metadata["cpi_source"],
             "Use": source_metadata["cpi_series"]},
            {"Source": "USD/INR", "File": "data/processed/usd_inr_monthly_clean.csv",
             "Use": "Monthly INR per USD source levels"},
            {"Source": "Brent", "File": "data/processed/brent_monthly_clean.csv",
             "Use": "Monthly USD/barrel source levels"},
        ]
    )
    feature_rows = pd.DataFrame(
        [
            {
                "Configuration": configuration,
                "Predictor groups": ", ".join(FEATURE_COLUMNS[configuration]),
                "Feature count": len(FEATURE_COLUMNS[configuration]),
            }
            for configuration in CONFIGURATIONS
        ]
    )
    feature_details = pd.DataFrame(
        [
            {
                "Feature": "CPI published-inflation lags",
                "Construction": "y[t-1], y[t-3], y[t-6], y[t-12]",
                "Rationale": "Inflation persistence and recent price level",
                "Availability/leakage control": "Published CPI history only through t-1",
            },
            {
                "Feature": "CPI change, trailing mean, trailing volatility",
                "Construction": "y[t-1]-y[t-2]; mean of y[t-1:t-3]; sample SD of y[t-1:t-6]",
                "Rationale": "Recent acceleration, level, and instability",
                "Availability/leakage control": "Trailing windows end at t-1; no centered windows",
            },
            {
                "Feature": "USD/INR one-month log return",
                "Construction": "100 * (ln(FX[t-1]) - ln(FX[t-2]))",
                "Rationale": "Positive values indicate INR depreciation",
                "Availability/leakage control": (
                    "Source reference months precede origin; no future FX"
                ),
            },
            {
                "Feature": "USD/INR three-month cumulative return",
                "Construction": "Sum of three consecutive monthly FX log returns through t-1",
                "Rationale": "Accumulated depreciation/appreciation",
                "Availability/leakage control": "No gap bridging; all three months precede origin",
            },
            {
                "Feature": "USD/INR six-month volatility",
                "Construction": "Sample SD of six consecutive monthly FX log returns through t-1",
                "Rationale": "Recent exchange-rate instability",
                "Availability/leakage control": "Trailing window ends at t-1",
            },
            {
                "Feature": "Brent USD log returns",
                "Construction": "100 * log change in USD/barrel level; one-month and 3-month sum",
                "Rationale": "Lagged international oil-cost signal",
                "Availability/leakage control": "Only source levels dated no later than t-1",
            },
            {
                "Feature": "Brent-INR proxy log returns",
                "Construction": (
                    "Brent USD/barrel * USD/INR, then one-month and 3-month log changes"
                ),
                "Rationale": "Approximate rupee cost proxy for an oil barrel",
                "Availability/leakage control": (
                    "Lagged through t-1; not actual landed import cost; mechanically embeds FX"
                ),
            },
        ]
    )
    class_sensitivity: list[dict[str, Any]] = []
    target, _, _ = load_stage4_sources()
    for horizon in HORIZONS:
        frame = pd.read_csv(DATA_OUTPUT / "stage4_feature_matrix.csv")
        selected = frame.loc[
            frame["configuration"].eq("C0") & frame["horizon_months"].eq(horizon)
        ]
        for threshold in (4.0, 6.0, 8.0):
            class_sensitivity.append(
                {
                    "horizon_months": horizon,
                    "threshold_percent_strictly_greater": threshold,
                    "eligible_n": len(selected),
                    "elevated": int((selected["target_inflation"] > threshold).sum()),
                    "non_elevated": int((selected["target_inflation"] <= threshold).sum()),
                }
            )
    class_table = pd.DataFrame(class_sensitivity)
    feature_report = f"""# Stage 4 Data and Feature Report

## Evidence and scope

The pipeline reads existing processed source files only. It does not modify source datasets,
prior-stage outputs, or the shared feature-engineering module. No synthetic observations are
created. Source release timestamps and historical vintages remain unverified, so this is a
retrospective, reference-month-safe analysis rather than a real-time backtest.

{_markdown_table(source_rows)}

The target is the published All India / Combined / CPI (General) `inflation_value`. The CPI
index is not substituted. The selected continuous segment is {source_metadata['cpi_segment_start']}
through {source_metadata['cpi_segment_end']} ({source_metadata['cpi_observations']} months);
the 2025 gap and separate 2026 segment are excluded.

## Outcome and feature samples

For horizon `h`, each row predicts the published inflation rate in `target_month`, which equals
`forecast_origin + h`. A target is elevated exactly when it is strictly greater than 6.0%;
the exact 6.0% boundary is non-elevated. All feature reference months end at
`forecast_origin - 1`.

{_markdown_table(pd.DataFrame([
    {
        "Set": key,
        "N": value["observations"],
        "Elevated": value["elevated"],
        "Non-elevated": value["non_elevated"],
        "Origin start": value["origin_start"],
        "Origin end": value["origin_end"],
        "Target start": value["target_start"],
        "Target end": value["target_end"],
    }
    for key, value in coverage.items()
]))}

## Prespecified configurations

{_markdown_table(feature_rows)}

## Feature construction, rationale, and timing

{_markdown_table(feature_details)}

C0 is CPI history only. C1 adds lagged USD/INR information. C2 adds lagged Brent USD movements
to C1. C3 adds the lagged Brent-INR product proxy to C1 as an alternative imported-cost signal.
The proxy mechanically combines Brent USD/barrel and USD/INR; it is not actual landed import
cost and excludes freight, insurance, taxes, contracts, quality, and other costs. The feature
matrix recomputes calendar-safe returns and trailing summaries from unchanged source levels;
it does not use the pre-engineered, unit-ambiguous Brent volatility field.

The primary features are CPI lags at 1, 3, 6, and 12 months, a one-month change, a trailing
three-month mean and six-month standard deviation; USD/INR one-month log return, trailing
three-month cumulative log return and six-month return volatility; and, in C2/C3, one-month and
three-month Brent or Brent-INR proxy log returns. All trailing windows end at `t-1`. The FX sign
is explicit: a positive log return means INR depreciation. No repo, NEER/REER, WPI, realized
future FX, prior-stage predictions, or target-month predictors enter the primary model.

## Timing and data integrity checks

- Every target month equals the origin plus the stated horizon; each predictor ends before origin.
- CPI source months are unique and the selected published series is consecutive.
- Market source levels are aligned by calendar month and missing months are rejected, not filled.
- All four configurations share identical origins and target months within each horizon.
- Data source and prior-stage integrity hashes are recorded in
  `artifacts/metrics/early_warning/stage4_run_metadata.json`.
"""
    (REPORT_OUTPUT / "STAGE4_DATA_AND_FEATURE_REPORT.md").write_text(
        feature_report, encoding="utf-8"
    )

    model_report = f"""# Stage 4 Model Results Report

## Models and selection

Regularized logistic regression, a shallow Random Forest, and a constrained XGBoost classifier
were fit. Hyperparameters were selected using only expanding-origin validation predictions.
Scaling is inside the logistic-regression fold pipeline; class balancing is calculated from
each training fold. Thresholds maximize validation F1, with ties resolved toward fewer false
alarms and then the higher threshold. The final test was not used for model selection.

## Final-test metrics

Undefined metrics are shown as `NA`; the saved CSV uses an explicit `NA` marker. The final test
contains only 18 monthly targets and three elevated months per horizon, so point estimates are
descriptive and unstable.

{_markdown_table(test_metrics, ["horizon_months", "configuration", "model", "n",
    "actual_positive", "predicted_positive", "precision", "recall", "f1",
    "pr_auc_average_precision", "roc_auc", "brier_score", "false_positive_rate",
    "false_negative_rate", "false_alarms_per_year", "actual_elevated_episodes",
    "detected_elevated_episodes", "missed_elevated_episodes", "false_alarm_episodes",
    "episode_sensitivity"])}

## Calibration summary

The following four-bin summaries are descriptive only. With 18 test observations and three
positive labels per horizon, empty or sparsely populated bins are expected and do not support
strong calibration claims.

{_markdown_table(calibration)}

## Validation-selected specification by horizon

The selection below uses validation average precision, then validation Brier score as a
tie-breaker. It is not a ranking selected from final-test results.

{_markdown_table(validation_selection.loc[validation_selection["overall_horizon_selected"]],
    ["horizon_months", "configuration", "model", "candidate_id",
     "validation_pr_auc_average_precision", "selected_threshold", "f1", "brier_score"])}

### Held-out results for the validation-selected models

{_markdown_table(
    validation_selection.loc[validation_selection["overall_horizon_selected"]][
        ["horizon_months", "configuration", "model"]
    ].merge(
        test_metrics,
        on=["horizon_months", "configuration", "model"],
        validate="one_to_one",
    ),
    ["horizon_months", "configuration", "model", "n", "actual_positive",
     "precision", "recall", "f1", "pr_auc_average_precision", "roc_auc",
     "brier_score", "false_positive", "false_negative",
     "detected_elevated_episodes", "missed_elevated_episodes",
     "false_alarm_episodes"],
)}

The final-test table includes every model/configuration combination with a common target sample.
The validation-selected entry is the appropriate horizon-level specification to discuss;
test-set leaders are not promoted to selected models.

No statistical significance test was used. The small test event count and serial/overlapping
outcomes do not justify IID significance claims. These models estimate predictive associations,
not causal effects.
"""
    (REPORT_OUTPUT / "STAGE4_MODEL_RESULTS_REPORT.md").write_text(
        model_report, encoding="utf-8"
    )

    evaluation_report = f"""# Stage 4 Evaluation and Robustness Report

## Chronological evaluation

{_markdown_table(split_counts)}

Each validation prediction is generated at its origin from an expanding training sample whose
labels have target months strictly earlier than that origin. Final models are refit once at the
first test origin with the same maturity rule, then frozen over the test. The January-June 2023
target block is not scored for tuning or final testing. Consecutive 3- and 6-month direct
forecast targets overlap in information and are dependent; the final sample has only 18
observations and three elevated months in two episodes.

## Incremental predictive value

Positive `delta_pr_auc_vs_c0` indicates higher average precision than C0, while positive
`delta_brier_vs_c0` indicates worse Brier score. Each difference is paired by identical target
month for the same classifier.

{_markdown_table(incremental)}

These are descriptive prediction comparisons, not evidence that a feature has or lacks a causal
economic effect. Brent-INR is an approximate product proxy, not landed import cost.

## Error, episode, and threshold diagnostics

The saved test metrics report precision, recall, F1, average precision (PR-AUC), ROC-AUC, Brier
score, calibration-relevant probabilities, confusion counts, false-positive/negative rates,
false alarms per year, and episode sensitivity. Direct forecast warning lead is the nominal
horizon `h`; it is not interpreted as causal lead time. Missed elevated outcomes are missed
warnings, while false positives are attention-consuming alarms. No policy cost ratio is assumed.

{_markdown_table(class_table)}

The >4% and >8% values are label-count sensitivities only and did not replace or retune the
primary >6% label. An 8% elevated class is too sparse for supervised evaluation in the eligible
period. Brier score is retained for one-class samples, but would not alone establish calibration.
Metrics requiring an absent class or denominator are `NA`, with counts and reasons recorded.

## Reproducibility and protected integrity

Seed: {SEED}. Python: {platform.python_version()}. Successful model fitting raises an error if
Logistic Regression emits a convergence warning. Protected inputs/files were hashed before and
after the pipeline; {len(protected_before)} pre-existing files are covered. Consecutive pipeline
output hashes are compared independently after two complete runs. Prediction/metric file
reproducibility is distinct from byte-for-byte serialization reproducibility of fitted model
artifacts.

The pipeline also writes horizon-specific target files, a row-level origin/split manifest,
and a feature-eligibility table under `data/processed/stage4/` and
`artifacts/metrics/early_warning/`. Diagnostic figures include class distribution, observed
episodes, PR/ROC curves, confusion matrices, calibration, selected-model feature importance,
configuration comparisons, and final-test warning timelines under
`visualizations/early_warning/`.

## Feature-importance evidence

Importance is model-specific descriptive association, not causal contribution. Logistic
coefficients are in standardized input units; tree importances are impurity/split importances.
They must not be interpreted as structural economic effects.

{_markdown_table(feature_importance.head(30))}
"""
    (REPORT_OUTPUT / "STAGE4_EVALUATION_AND_ROBUSTNESS_REPORT.md").write_text(
        evaluation_report, encoding="utf-8"
    )

    selected = validation_selection.loc[validation_selection["overall_horizon_selected"]]
    final_report = f"""# Stage 4 Final Research Report

## Executive assessment

**Classification: VERIFIED WITH LIMITATIONS.** The Stage 4 implementation and retrospective
evaluation completed using the verified published-CPI segment, origin-safe lagged predictors,
chronological validation, and an untouched common final-test target window. This does not
establish real-time deployability, causal effects, or reliable operational warning performance.

## Selected models and observed results

Models/configurations were selected using validation average precision and Brier-score tie
breaks, not test outcomes. Their held-out metrics are linked below.

{_markdown_table(selected, ["horizon_months", "configuration", "model", "candidate_id",
    "validation_pr_auc_average_precision", "selected_threshold"])}

The full final-test comparison is in
[STAGE4_MODEL_RESULTS_REPORT.md](./STAGE4_MODEL_RESULTS_REPORT.md).
The test contains only 18 observations and three elevated months (two episodes) per horizon.
The >6% classification boundary is strict; 6.0% is non-elevated.

Stage 2 and Stage 3 remain **VERIFIED WITH LIMITATIONS**; their retrospective and
non-causal constraints remain in force. Stage 4 does not use prior-stage fitted predictions
as predictors.

## Evidence and integrity

- Input target: published All India / Combined / CPI (General) `inflation_value`;
  CPI index substitution: no.
- Target period: January 2014-December 2024, 132 consecutive months; no 2025 gap bridging.
- All predictor reference dates precede their forecast origins; future realized
  FX/Brent/CPI values are not predictors.
- C0/C1/C2/C3 are same-origin/same-target ablations and are described in
  [STAGE4_DATA_AND_FEATURE_REPORT.md](./STAGE4_DATA_AND_FEATURE_REPORT.md).
- Prior-stage outputs and raw/existing processed data are protected by before/after hashes.
- Horizon-specific target datasets, an origin/split manifest, and feature eligibility details
  are generated for auditability.
- Final-test diagnostics are saved for class counts, episodes, PR/ROC, confusion matrices,
  calibration, feature importance, configuration comparisons, and risk timelines.
- No synthetic data, deep learning, dashboard, or Stage 5 work was performed.

## Limitations carried forward

1. The final test has only three elevated target months in two episodes; discrimination,
   calibration, model rankings, and episode sensitivity are highly uncertain.
2. CPI year-on-year observations and 3-/6-month horizon outcomes overlap; monthly rows
   are dependent.
3. Historical release dates and data vintages are unavailable. Reference-month lagging is not proof
   of actual real-time availability.
4. The Brent-INR variable is a mechanical, approximate product proxy and not landed import cost.
5. Repo, NEER/REER, and WPI are excluded from primary models because provenance/timing was not
   sufficiently resolved.
6. Predictive feature importance and incremental scores are not causal evidence.
7. Threshold selection and validation metrics are themselves uncertain on a small episodic sample.

See [STAGE4_EVALUATION_AND_ROBUSTNESS_REPORT.md](./STAGE4_EVALUATION_AND_ROBUSTNESS_REPORT.md)
for paired comparisons, errors, episode findings, and reproducibility details. Stage 5 has not
been started; stop for researcher review.
"""
    (REPORT_OUTPUT / "STAGE4_FINAL_RESEARCH_REPORT.md").write_text(
        final_report, encoding="utf-8"
    )


def run_experiments() -> None:
    """Run feature construction, chronological selection, final evaluation, and reporting."""
    for path in (
        DATA_OUTPUT,
        MODEL_OUTPUT,
        PREDICTION_OUTPUT,
        METRIC_OUTPUT,
        VISUALIZATION_OUTPUT,
    ):
        path.mkdir(parents=True, exist_ok=True)
    protected_before = _protected_hashes()
    target, market, source_metadata = load_stage4_sources()
    frames, coverage = build_classification_frames(target, market)
    dataset = pd.concat(
        [
            frame.assign(configuration=configuration)
            for (configuration, _), frame in frames.items()
        ],
        ignore_index=True,
    ).sort_values(["horizon_months", "configuration", "forecast_origin"])
    dataset.to_csv(DATA_OUTPUT / "stage4_feature_matrix.csv", index=False, na_rep="NA")
    (DATA_OUTPUT / "stage4_feature_definitions.json").write_text(
        json.dumps(FEATURE_COLUMNS, indent=2, sort_keys=True), encoding="utf-8"
    )
    for horizon in HORIZONS:
        target_dataset = frames[("C0", horizon)][
            [
                "forecast_origin",
                "target_month",
                "horizon_months",
                "target_inflation",
                "elevated_target",
            ]
        ]
        target_dataset.to_csv(
            DATA_OUTPUT / f"stage4_target_h{horizon}.csv",
            index=False,
            na_rep="NA",
        )
    _feature_eligibility_table().to_csv(
        DATA_OUTPUT / "stage4_feature_eligibility.csv",
        index=False,
    )

    grid = candidate_grid()
    selection_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []
    final_prediction_rows: list[dict[str, Any]] = []
    test_metric_rows: list[dict[str, Any]] = []
    model_importance_rows: list[dict[str, Any]] = []
    final_estimators: dict[str, Any] = {}
    split_count_rows: list[dict[str, Any]] = []
    candidate_predictions: dict[tuple[str, int, str, str], pd.DataFrame] = {}
    candidate_objects: dict[tuple[str, int, str, str], Candidate] = {}

    for configuration in CONFIGURATIONS:
        for horizon in HORIZONS:
            frame = frames[(configuration, horizon)]
            features = FEATURE_COLUMNS[configuration]
            split_count_rows.extend(_split_counts(frame, horizon))
            for model_name, candidates in grid.items():
                candidate_scores: list[dict[str, Any]] = []
                for candidate in candidates:
                    validation_data = predict_candidate(
                        candidate,
                        features,
                        validation_frame(frame, horizon),
                        SEED,
                    )
                    validation_data["horizon_months"] = horizon
                    candidate_predictions[
                        (configuration, horizon, model_name, candidate.candidate_id)
                    ] = validation_data
                    candidate_objects[
                        (configuration, horizon, model_name, candidate.candidate_id)
                    ] = candidate
                    metrics, threshold = _candidate_metrics(candidate, validation_data)
                    metrics.update(
                        {
                            "configuration": configuration,
                            "horizon_months": horizon,
                            "model": model_name,
                            "parameters": json.dumps(candidate.parameters, sort_keys=True),
                        }
                    )
                    candidate_scores.append(metrics)
                chosen = sorted(
                    candidate_scores,
                    key=lambda row: (
                        -row["validation_pr_auc_average_precision"],
                        row["brier_score"],
                        row["candidate_id"],
                    ),
                )[0]
                chosen_candidate = candidate_objects[
                    (
                        configuration,
                        horizon,
                        model_name,
                        chosen["candidate_id"],
                    )
                ]
                chosen_validation = candidate_predictions[
                    (configuration, horizon, model_name, chosen["candidate_id"])
                ].copy()
                threshold = float(chosen["validation_threshold"])
                selection_rows.append(
                    {
                        **chosen,
                        "selected_parameters": json.dumps(
                            chosen_candidate.parameters, sort_keys=True
                        ),
                        "selected_threshold": threshold,
                    }
                )
                for row in chosen_validation.itertuples(index=False):
                    final_prediction_rows.append(
                        {
                            "partition": "expanding_validation",
                            "configuration": configuration,
                            "model": model_name,
                            "horizon_months": horizon,
                            "candidate_id": chosen_candidate.candidate_id,
                            "forecast_origin": row.forecast_origin,
                            "target_month": row.target_month,
                            "actual_inflation_class": row.actual,
                            "predicted_probability": row.probability,
                            "selected_validation_threshold": threshold,
                            "predicted_alert": int(row.probability >= threshold),
                            "validation_training_n": row.validation_training_n,
                            "validation_training_positive": row.validation_training_positive,
                        }
                    )

                validation_rows.append(
                    {
                        "configuration": configuration,
                        "model": model_name,
                        "horizon_months": horizon,
                        "candidate_id": chosen_candidate.candidate_id,
                        "selected_threshold": threshold,
                        "validation_n": int(chosen["n"]),
                        "validation_elevated": int(chosen["actual_positive"]),
                        "validation_predicted_positive": int(chosen["predicted_positive"]),
                        "validation_precision": chosen["precision"],
                        "validation_recall": chosen["recall"],
                        "validation_f1": chosen["f1"],
                        "validation_pr_auc_average_precision": chosen[
                            "validation_pr_auc_average_precision"
                        ],
                        "validation_roc_auc": chosen["roc_auc"],
                        "validation_brier_score": chosen["brier_score"],
                        "validation_false_positive_rate": chosen["false_positive_rate"],
                        "validation_false_negative_rate": chosen["false_negative_rate"],
                    }
                )

                first_test_origin = frame.loc[
                    frame["target_month"].between(TEST_START, TEST_END), "forecast_origin"
                ].min()
                training = frame.loc[frame["target_month"] < first_test_origin].sort_values(
                    "forecast_origin"
                )
                if training.empty or training["elevated_target"].nunique() != 2:
                    raise ValueError(
                        f"Final training data lack both classes for {configuration}, "
                        f"{model_name}, {horizon}m."
                    )
                estimator = fit_candidate(
                    chosen_candidate,
                    features,
                    training,
                    training["elevated_target"].astype(int),
                    SEED,
                )
                test = frame.loc[frame["target_month"].between(TEST_START, TEST_END)].copy()
                probabilities = estimator.predict_proba(test[features])[:, 1]
                test["probability"] = probabilities
                test["predicted_alert"] = (probabilities >= threshold).astype(int)
                metric = classification_metrics(
                    test["elevated_target"].to_numpy(dtype=int),
                    probabilities,
                    threshold,
                    horizon,
                    test["target_month"],
                )
                test_metric_rows.append(
                    {
                        **metric,
                        "configuration": configuration,
                        "model": model_name,
                        "horizon_months": horizon,
                        "candidate_id": chosen_candidate.candidate_id,
                        "threshold": threshold,
                        "validation_pr_auc_average_precision": chosen[
                            "validation_pr_auc_average_precision"
                        ],
                        "test_target_start": test["target_month"].min().date().isoformat(),
                        "test_target_end": test["target_month"].max().date().isoformat(),
                    }
                )
                for row in test.itertuples(index=False):
                    final_prediction_rows.append(
                        {
                            "partition": "untouched_final_test",
                            "configuration": configuration,
                            "model": model_name,
                            "horizon_months": horizon,
                            "candidate_id": chosen_candidate.candidate_id,
                            "forecast_origin": row.forecast_origin,
                            "target_month": row.target_month,
                            "actual_inflation_class": row.elevated_target,
                            "actual_inflation": row.target_inflation,
                            "predicted_probability": row.probability,
                            "selected_validation_threshold": threshold,
                            "predicted_alert": row.predicted_alert,
                            "validation_training_n": len(training),
                            "validation_training_positive": int(training["elevated_target"].sum()),
                        }
                    )
                key = f"{configuration}|{horizon}|{model_name}"
                final_estimators[key] = estimator
                if model_name == "logistic_regression":
                    coefficients = estimator.named_steps["classifier"].coef_[0]
                    importance_values = coefficients
                    importance_method = "standardized_logistic_coefficient"
                else:
                    importance_values = estimator.feature_importances_
                    importance_method = "tree_feature_importance"
                model_importance_rows.extend(
                    {
                        "configuration": configuration,
                        "model": model_name,
                        "horizon_months": horizon,
                        "feature": feature,
                        "importance": float(value),
                        "importance_method": importance_method,
                    }
                    for feature, value in zip(features, importance_values, strict=True)
                )
            baseline_id = "majority_prevalence"
            validation_start = pd.Timestamp("2021-01-01") + pd.DateOffset(months=horizon)
            validation_rows_for_baseline = frame.loc[
                frame["target_month"].between(validation_start, pd.Timestamp("2022-12-01"))
            ].sort_values("forecast_origin")
            baseline_validation_rows: list[dict[str, Any]] = []
            for row in validation_rows_for_baseline.itertuples(index=False):
                mature_training = frame.loc[frame["target_month"] < row.forecast_origin]
                if mature_training.empty:
                    raise ValueError(f"No mature labels for baseline at {row.forecast_origin}.")
                baseline_validation_rows.append(
                    {
                        "forecast_origin": row.forecast_origin,
                        "target_month": row.target_month,
                        "actual": int(row.elevated_target),
                        "probability": float(mature_training["elevated_target"].mean()),
                        "validation_training_n": len(mature_training),
                        "validation_training_positive": int(
                            mature_training["elevated_target"].sum()
                        ),
                        "horizon_months": horizon,
                    }
                )
                final_prediction_rows.append(
                    {
                        "partition": "expanding_validation",
                        "configuration": configuration,
                        "model": "prevalence_baseline",
                        "horizon_months": horizon,
                        "candidate_id": baseline_id,
                        "forecast_origin": row.forecast_origin,
                        "target_month": row.target_month,
                        "actual_inflation_class": int(row.elevated_target),
                        "predicted_probability": float(
                            mature_training["elevated_target"].mean()
                        ),
                        "selected_validation_threshold": 0.5,
                        "predicted_alert": int(
                            mature_training["elevated_target"].mean() >= 0.5
                        ),
                        "validation_training_n": len(mature_training),
                        "validation_training_positive": int(
                            mature_training["elevated_target"].sum()
                        ),
                    }
                )
            baseline_validation = pd.DataFrame(baseline_validation_rows)
            baseline_result = classification_metrics(
                baseline_validation["actual"].to_numpy(dtype=int),
                baseline_validation["probability"].to_numpy(dtype=float),
                0.5,
                horizon,
                baseline_validation["target_month"],
            )
            validation_rows.append(
                {
                    "configuration": configuration,
                    "model": "prevalence_baseline",
                    "horizon_months": horizon,
                    "candidate_id": baseline_id,
                    "selected_threshold": 0.5,
                    "validation_n": baseline_result["n"],
                    "validation_elevated": baseline_result["actual_positive"],
                    "validation_predicted_positive": baseline_result["predicted_positive"],
                    "validation_precision": baseline_result["precision"],
                    "validation_recall": baseline_result["recall"],
                    "validation_f1": baseline_result["f1"],
                    "validation_pr_auc_average_precision": baseline_result[
                        "pr_auc_average_precision"
                    ],
                    "validation_roc_auc": baseline_result["roc_auc"],
                    "validation_brier_score": baseline_result["brier_score"],
                    "validation_false_positive_rate": baseline_result[
                        "false_positive_rate"
                    ],
                    "validation_false_negative_rate": baseline_result[
                        "false_negative_rate"
                    ],
                    "validation_undefined_metric_notes": baseline_result[
                        "undefined_metric_notes"
                    ],
                }
            )
            first_test_origin = frame.loc[
                frame["target_month"].between(TEST_START, TEST_END), "forecast_origin"
            ].min()
            mature_training = frame.loc[frame["target_month"] < first_test_origin]
            baseline_probability = float(mature_training["elevated_target"].mean())
            test = frame.loc[frame["target_month"].between(TEST_START, TEST_END)].copy()
            test_probabilities = np.full(len(test), baseline_probability, dtype=float)
            baseline_result = classification_metrics(
                test["elevated_target"].to_numpy(dtype=int),
                test_probabilities,
                0.5,
                horizon,
                test["target_month"],
            )
            test_metric_rows.append(
                {
                    **baseline_result,
                    "configuration": configuration,
                    "model": "prevalence_baseline",
                    "horizon_months": horizon,
                    "candidate_id": baseline_id,
                    "threshold": 0.5,
                    "validation_pr_auc_average_precision": np.nan,
                    "test_target_start": test["target_month"].min().date().isoformat(),
                    "test_target_end": test["target_month"].max().date().isoformat(),
                }
            )
            for row in test.itertuples(index=False):
                final_prediction_rows.append(
                    {
                        "partition": "untouched_final_test",
                        "configuration": configuration,
                        "model": "prevalence_baseline",
                        "horizon_months": horizon,
                        "candidate_id": baseline_id,
                        "forecast_origin": row.forecast_origin,
                        "target_month": row.target_month,
                        "actual_inflation_class": int(row.elevated_target),
                        "actual_inflation": row.target_inflation,
                        "predicted_probability": baseline_probability,
                        "selected_validation_threshold": 0.5,
                        "predicted_alert": int(baseline_probability >= 0.5),
                        "validation_training_n": len(mature_training),
                        "validation_training_positive": int(
                            mature_training["elevated_target"].sum()
                        ),
                    }
                )

    selection = pd.DataFrame(selection_rows)
    selected_for_horizon: list[int] = []
    for horizon in HORIZONS:
        candidates = selection.loc[selection["horizon_months"].eq(horizon)].sort_values(
            [
                "validation_pr_auc_average_precision",
                "brier_score",
                "configuration",
                "model",
            ],
            ascending=[False, True, True, True],
        )
        selected_for_horizon.append(int(candidates.index[0]))
    selection["overall_horizon_selected"] = selection.index.isin(selected_for_horizon)

    validation_metrics = pd.DataFrame(validation_rows).merge(
        selection[
            [
                "configuration",
                "model",
                "horizon_months",
                "candidate_id",
                "true_positive",
                "false_positive",
                "true_negative",
                "false_negative",
                "false_alarms_per_year",
                "episode_sensitivity",
                "overall_horizon_selected",
            ]
        ],
        on=["configuration", "model", "horizon_months", "candidate_id"],
        how="left",
        validate="one_to_one",
    )
    validation_metrics = validation_metrics.rename(
        columns={
            "true_positive": "validation_tp",
            "false_positive": "validation_fp",
            "true_negative": "validation_tn",
            "false_negative": "validation_fn",
            "false_alarms_per_year": "validation_false_alarms_per_year",
            "episode_sensitivity": "validation_episode_sensitivity",
        }
    )
    validation_metrics["overall_horizon_selected"] = (
        validation_metrics["overall_horizon_selected"].fillna(False).astype(bool)
    )
    test_metrics = pd.DataFrame(test_metric_rows)
    predictions = pd.DataFrame(final_prediction_rows).sort_values(
        ["partition", "horizon_months", "configuration", "model", "forecast_origin"]
    )
    test_only = predictions.loc[predictions["partition"].eq("untouched_final_test")]
    incremental_rows: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        for model in (*grid, "prevalence_baseline"):
            baseline = test_only.loc[
                test_only["horizon_months"].eq(horizon)
                & test_only["configuration"].eq("C0")
                & test_only["model"].eq(model)
            ].set_index("target_month")
            for configuration in ("C1", "C2", "C3"):
                extended = test_only.loc[
                    test_only["horizon_months"].eq(horizon)
                    & test_only["configuration"].eq(configuration)
                    & test_only["model"].eq(model)
                ].set_index("target_month")
                common = baseline.index.intersection(extended.index).sort_values()
                c0_metrics = test_metrics.loc[
                    test_metrics["configuration"].eq("C0")
                    & test_metrics["model"].eq(model)
                    & test_metrics["horizon_months"].eq(horizon)
                ].iloc[0]
                extended_metrics = test_metrics.loc[
                    test_metrics["configuration"].eq(configuration)
                    & test_metrics["model"].eq(model)
                    & test_metrics["horizon_months"].eq(horizon)
                ].iloc[0]
                incremental_rows.append(
                    {
                        "horizon_months": horizon,
                        "model": model,
                        "baseline_configuration": "C0",
                        "extended_configuration": configuration,
                        "common_n": len(common),
                        "common_target_start": common.min().date().isoformat(),
                        "common_target_end": common.max().date().isoformat(),
                        "c0_pr_auc_average_precision": c0_metrics[
                            "pr_auc_average_precision"
                        ],
                        "extended_pr_auc_average_precision": extended_metrics[
                            "pr_auc_average_precision"
                        ],
                        "delta_pr_auc_vs_c0": (
                            extended_metrics["pr_auc_average_precision"]
                            - c0_metrics["pr_auc_average_precision"]
                        ),
                        "c0_brier_score": c0_metrics["brier_score"],
                        "extended_brier_score": extended_metrics["brier_score"],
                        "delta_brier_vs_c0": (
                            extended_metrics["brier_score"] - c0_metrics["brier_score"]
                        ),
                        "c0_precision": c0_metrics["precision"],
                        "extended_precision": extended_metrics["precision"],
                        "c0_recall": c0_metrics["recall"],
                        "extended_recall": extended_metrics["recall"],
                        "c0_f1": c0_metrics["f1"],
                        "extended_f1": extended_metrics["f1"],
                        "comparison_scope": (
                            "paired identical target months; separate validation-selected fits"
                        ),
                    }
                )
    incremental = pd.DataFrame(incremental_rows)
    split_counts = pd.DataFrame(
        [
            row
            for horizon in HORIZONS
            for row in _split_counts(frames[("C0", horizon)], horizon)
        ]
    )
    origin_manifest = pd.concat(
        [
            _origin_split_manifest(frames[("C0", horizon)], horizon)
            for horizon in HORIZONS
        ],
        ignore_index=True,
    )
    importance = pd.DataFrame(model_importance_rows).sort_values(
        ["horizon_months", "configuration", "model", "feature"]
    )
    calibration = _calibration_bins(
        test_only,
        selection,
    )

    prediction_path = PREDICTION_OUTPUT / "stage4_early_warning_predictions.csv"
    predictions.to_csv(prediction_path, index=False, na_rep="NA", float_format="%.12g")
    validation_metrics.to_csv(
        METRIC_OUTPUT / "stage4_validation_metrics.csv",
        index=False,
        na_rep="NA",
        float_format="%.12g",
    )
    test_metrics.to_csv(
        METRIC_OUTPUT / "stage4_test_metrics.csv",
        index=False,
        na_rep="NA",
        float_format="%.12g",
    )
    incremental.to_csv(
        METRIC_OUTPUT / "stage4_incremental_comparisons.csv",
        index=False,
        na_rep="NA",
        float_format="%.12g",
    )
    selection.to_csv(
        METRIC_OUTPUT / "stage4_model_selection.csv",
        index=False,
        na_rep="NA",
        float_format="%.12g",
    )
    split_counts.to_csv(METRIC_OUTPUT / "stage4_class_counts.csv", index=False)
    origin_manifest.to_csv(
        METRIC_OUTPUT / "stage4_origin_split_manifest.csv",
        index=False,
        na_rep="NA",
    )
    importance.to_csv(
        METRIC_OUTPUT / "stage4_feature_importance.csv",
        index=False,
        na_rep="NA",
        float_format="%.12g",
    )
    calibration.to_csv(
        METRIC_OUTPUT / "stage4_calibration_bins.csv",
        index=False,
        na_rep="NA",
        float_format="%.12g",
    )
    joblib.dump(final_estimators, MODEL_OUTPUT / "stage4_final_models.joblib", compress=3)
    model_specs = selection[
        [
            "configuration",
            "horizon_months",
            "model",
            "candidate_id",
            "selected_parameters",
            "selected_threshold",
            "validation_pr_auc_average_precision",
            "brier_score",
            "overall_horizon_selected",
        ]
    ].to_dict(orient="records")
    (MODEL_OUTPUT / "stage4_model_specifications.json").write_text(
        json.dumps(model_specs, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    _write_visualizations(
        target,
        predictions,
        test_metrics,
        selection,
        importance,
        calibration,
    )

    metadata = {
        "stage": "Stage 4 Early Warning Classification",
        "seed": SEED,
        "python": platform.python_version(),
        "package_versions": {
            package: _package_version(package)
            for package in ("numpy", "pandas", "scikit-learn", "xgboost", "joblib", "matplotlib")
        },
        "source_metadata": source_metadata,
        "feature_coverage": coverage,
        "model_search": {
            name: [
                {"candidate_id": candidate.candidate_id, "parameters": candidate.parameters}
                for candidate in candidates
            ]
            for name, candidates in grid.items()
        },
        "protected_preexisting_file_count": len(protected_before),
        "protected_file_sha256": protected_before,
        "protected_hashes_sha256": hashlib.sha256(
            json.dumps(protected_before, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "raw_existing_processed_and_prior_stage_files_modified": False,
        "logistic_convergence_warnings": 0,
        "synthetic_observations_created": 0,
        "release_vintages_verified": False,
        "interpretation": "Retrospective predictive associations; no causal claims.",
    }
    (METRIC_OUTPUT / "stage4_run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    _write_reports(
        source_metadata,
        coverage,
        split_counts,
        selection,
        test_metrics,
        incremental,
        protected_before,
        importance,
        calibration,
    )
    protected_after = _protected_hashes()
    if protected_after != protected_before:
        changed = sorted(
            key
            for key in set(protected_before) | set(protected_after)
            if protected_before.get(key) != protected_after.get(key)
        )
        raise RuntimeError(f"Protected project files changed during Stage 4 run: {changed}")
    print(
        "Stage 4 pipeline complete: "
        f"{len(predictions)} prediction rows, {len(test_metrics)} final-test metric rows, "
        f"{len(protected_before)} protected files unchanged."
    )


if __name__ == "__main__":
    run_experiments()
