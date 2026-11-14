"""Evaluation metrics and paired configuration comparisons for CPI forecasts."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from statsmodels.stats.diagnostic import acorr_ljungbox


def forecast_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> dict[str, float]:
    """Calculate point forecast metrics with explicit MAPE stability checks."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if actual.ndim != 1 or predicted.shape != actual.shape or not len(actual):
        raise ValueError("Actual and predicted values must be non-empty 1D arrays of equal length.")
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("Actual and predicted values must be finite.")
    error = predicted - actual
    mape = (
        float(np.mean(np.abs(error / actual)) * 100.0)
        if np.all(np.abs(actual) >= 1.0)
        else float("nan")
    )
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(np.square(error)))),
        "r2": float(r2_score(actual, predicted)) if np.unique(actual).size > 1 else float("nan"),
        "bias": float(np.mean(error)),
        "mape": mape,
    }


def build_model_comparison(predictions: pd.DataFrame) -> pd.DataFrame:
    """Aggregate metrics with sample counts and target-period coverage."""
    rows: list[dict[str, Any]] = []
    group_columns = ["horizon", "configuration", "model"]
    for (horizon, configuration, model), group in predictions.groupby(group_columns, sort=True):
        metrics = forecast_metrics(
            group["actual"].to_numpy(),
            group["predicted"].to_numpy(),
        )
        rows.append(
            {
                "horizon": int(horizon),
                "configuration": configuration,
                "model": model,
                "n": len(group),
                "evaluation_start": group["target_date"].min().date().isoformat(),
                "evaluation_end": group["target_date"].max().date().isoformat(),
                **metrics,
            }
        )
    return pd.DataFrame(rows)


def build_incremental_comparison(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Compare C1/C2/C3 with C0 on identical model/horizon target dates."""
    rows: list[dict[str, Any]] = []
    model_predictions = predictions.loc[predictions["configuration"].isin(["C0", "C1", "C2", "C3"])]
    for (horizon, model), group in model_predictions.groupby(["horizon", "model"]):
        baseline = group.loc[group["configuration"].eq("C0")].set_index("target_date")
        if baseline.empty:
            continue
        for configuration in ("C1", "C2", "C3"):
            comparison = group.loc[group["configuration"].eq(configuration)].set_index(
                "target_date"
            )
            common_dates = baseline.index.intersection(comparison.index).sort_values()
            if common_dates.empty:
                rows.append(
                    {
                        "horizon": horizon,
                        "model": model,
                        "configuration": configuration,
                        "common_n": 0,
                        "comparison_status": "unavailable",
                        "delta_mae_vs_C0": np.nan,
                        "delta_rmse_vs_C0": np.nan,
                        "improvement": "unavailable",
                    }
                )
                continue
            actual = baseline.loc[common_dates, "actual"].to_numpy(dtype=float)
            c0_pred = baseline.loc[common_dates, "predicted"].to_numpy(dtype=float)
            config_pred = comparison.loc[common_dates, "predicted"].to_numpy(dtype=float)
            c0_metrics = forecast_metrics(actual, c0_pred)
            config_metrics = forecast_metrics(actual, config_pred)
            delta_mae = config_metrics["mae"] - c0_metrics["mae"]
            delta_rmse = config_metrics["rmse"] - c0_metrics["rmse"]
            rows.append(
                {
                    "horizon": horizon,
                    "model": model,
                    "configuration": configuration,
                    "common_n": len(common_dates),
                    "evaluation_start": common_dates.min().date().isoformat(),
                    "evaluation_end": common_dates.max().date().isoformat(),
                    "comparison_status": (
                        "paired_common_sample"
                        if len(common_dates) == len(baseline) == len(comparison)
                        else "common_sample_subset"
                    ),
                    "c0_mae": c0_metrics["mae"],
                    "configuration_mae": config_metrics["mae"],
                    "delta_mae_vs_C0": delta_mae,
                    "c0_rmse": c0_metrics["rmse"],
                    "configuration_rmse": config_metrics["rmse"],
                    "delta_rmse_vs_C0": delta_rmse,
                    "improvement": (
                        "improved"
                        if delta_mae < 0 and delta_rmse < 0
                        else "mixed"
                        if (delta_mae < 0) != (delta_rmse < 0)
                        else "worse_or_equal"
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_residual_diagnostics(predictions: pd.DataFrame) -> pd.DataFrame:
    """Summarize out-of-sample residual autocorrelation as an exploratory diagnostic."""
    rows: list[dict[str, Any]] = []
    for keys, group in predictions.groupby(["horizon", "configuration", "model"], sort=True):
        errors = group.sort_values("target_date")["error"].to_numpy(dtype=float)
        lag = min(6, max(1, len(errors) // 3))
        if len(errors) <= lag + 1:
            statistic = p_value = float("nan")
        else:
            result = acorr_ljungbox(errors, lags=[lag], return_df=True)
            statistic = float(result["lb_stat"].iloc[0])
            p_value = float(result["lb_pvalue"].iloc[0])
        rows.append(
            {
                "horizon": keys[0],
                "configuration": keys[1],
                "model": keys[2],
                "n": len(errors),
                "ljung_box_lag": lag,
                "ljung_box_statistic": statistic,
                "ljung_box_p_value": p_value,
                "interpretation_note": (
                    "exploratory; overlapping multi-step forecast errors are dependent"
                ),
            }
        )
    return pd.DataFrame(rows)


def build_episode_error_summary(
    predictions: pd.DataFrame,
    target_thresholds: dict[int, float],
    episode_type: str,
    episode_values: pd.DataFrame | None = None,
    value_thresholds: dict[int, float] | None = None,
) -> pd.DataFrame:
    """Summarize forecast errors for training-threshold-defined test episodes."""
    rows: list[dict[str, Any]] = []
    for horizon, group in predictions.groupby("horizon"):
        candidates = group.copy()
        if episode_type == "high_inflation":
            threshold = target_thresholds[horizon]
            candidates = candidates.loc[candidates["actual"] >= threshold]
            candidates["episode_value"] = candidates["actual"]
        elif episode_type == "brent_spike":
            if episode_values is None or value_thresholds is None:
                raise ValueError("Brent spike analysis requires values and training thresholds.")
            values = episode_values.loc[episode_values["horizon"].eq(horizon)]
            candidates = candidates.merge(
                values[["target_date", "diagnostic_value"]],
                on="target_date",
                how="inner",
                validate="many_to_one",
            )
            candidates = candidates.loc[candidates["diagnostic_value"] >= value_thresholds[horizon]]
            threshold = value_thresholds[horizon]
            candidates["episode_value"] = candidates["diagnostic_value"]
        else:
            raise ValueError(f"Unsupported episode type: {episode_type}")

        for (configuration, model), _ in group.groupby(
            ["configuration", "model"], sort=True
        ):
            selected = candidates.loc[
                candidates["configuration"].eq(configuration)
                & candidates["model"].eq(model)
            ]
            dates = pd.DatetimeIndex(selected["target_date"].drop_duplicates().sort_values())
            period_ordinals = dates.to_period("M").asi8
            n_episodes = (
                int(1 + np.count_nonzero(np.diff(period_ordinals) > 1))
                if len(period_ordinals)
                else 0
            )
            rows.append(
                {
                    "episode_type": episode_type,
                    "horizon": int(horizon),
                    "configuration": configuration,
                    "model": model,
                    "n_forecasts": len(selected),
                    "n_distinct_target_months": len(dates),
                    "n_episode_runs": n_episodes,
                    "threshold": target_thresholds[horizon]
                    if episode_type == "high_inflation"
                    else threshold,
                    "mae": float(np.mean(np.abs(selected["error"]))) if len(selected) else np.nan,
                    "rmse": float(np.sqrt(np.mean(selected["error"] ** 2)))
                    if len(selected)
                    else np.nan,
                    "bias": float(np.mean(selected["error"])) if len(selected) else np.nan,
                }
            )
    return pd.DataFrame(rows)
