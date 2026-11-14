"""Chronological Stage 2 models for published Indian CPI inflation."""

from __future__ import annotations

import pickle
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet, LinearRegression
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX
from xgboost import XGBRegressor

from src.forecasting.inflation.evaluation import (
    build_episode_error_summary,
    build_incremental_comparison,
    build_model_comparison,
    build_residual_diagnostics,
)

ROOT = Path(__file__).resolve().parents[3]
MODEL_ROOT = ROOT / "artifacts" / "models" / "inflation"
PREDICTION_ROOT = ROOT / "artifacts" / "predictions" / "inflation"
METRIC_ROOT = ROOT / "artifacts" / "metrics" / "inflation"
VISUALIZATION_ROOT = ROOT / "visualizations" / "inflation"
REPORT_ROOT = ROOT / "reports" / "experiments"

SEED = 42
HORIZONS = (1, 3, 6)
CONFIGURATIONS = ("C0", "C1", "C2", "C3")
ML_MODELS = ("elastic_net", "random_forest", "xgboost")
MODEL_NAMES = ("autoregression", "sarimax", *ML_MODELS)
SARIMAX_ORDER = (1, 0, 0)
SARIMAX_SEASONAL_ORDER = (0, 0, 0, 12)


def split_train_validation_test(
    frame: pd.DataFrame,
) -> tuple[pd.Index, pd.Index, pd.Index]:
    """Split eligible origin rows chronologically into 70/15/15 partitions."""
    n = len(frame)
    if n < 45:
        raise ValueError(f"At least 45 eligible CPI forecast origins are required; received {n}.")
    train_end = int(n * 0.70)
    validation_end = int(n * 0.85)
    return (
        pd.Index(range(train_end)),
        pd.Index(range(train_end, validation_end)),
        pd.Index(range(validation_end, n)),
    )


def _purged_cv_splits(
    frame: pd.DataFrame, n_splits: int = 3
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Build expanding folds, purging labels that are not known by validation origin."""
    splitter = TimeSeriesSplit(n_splits=n_splits)
    result: list[tuple[np.ndarray, np.ndarray]] = []
    for candidate_train, validation in splitter.split(frame):
        first_validation_origin = frame.iloc[validation[0]]["forecast_origin"]
        allowed_train = candidate_train[
            frame.iloc[candidate_train]["target_date"].to_numpy()
            < np.datetime64(first_validation_origin)
        ]
        if len(allowed_train) < 12:
            raise ValueError("Purged CPI cross-validation fold has fewer than 12 training rows.")
        result.append((allowed_train, validation))
    return result


def _model_and_grid(model_name: str) -> tuple[Any, dict[str, list[Any]]]:
    if model_name == "elastic_net":
        estimator = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "model",
                    ElasticNet(
                        max_iter=200_000,
                        tol=1e-5,
                        random_state=SEED,
                    ),
                ),
            ]
        )
        return estimator, {
            "model__alpha": [0.01, 0.1, 1.0],
            "model__l1_ratio": [0.1, 0.5, 0.9],
        }
    if model_name == "random_forest":
        return RandomForestRegressor(random_state=SEED, n_jobs=1), {
            "n_estimators": [100, 200],
            "max_depth": [2, 4],
            "min_samples_leaf": [2, 4],
        }
    if model_name == "xgboost":
        return XGBRegressor(
            random_state=SEED,
            objective="reg:squarederror",
            n_jobs=1,
        ), {
            "n_estimators": [100, 200],
            "max_depth": [2, 3],
            "learning_rate": [0.03, 0.06],
            "subsample": [0.8, 1.0],
        }
    raise ValueError(f"No tunable model configuration for {model_name}.")


def _tune_model(
    model_name: str,
    train_frame: pd.DataFrame,
    feature_columns: list[str],
) -> tuple[dict[str, Any], int]:
    estimator, grid = _model_and_grid(model_name)
    search = GridSearchCV(
        estimator,
        grid,
        cv=_purged_cv_splits(train_frame),
        scoring="neg_root_mean_squared_error",
        n_jobs=1,
        error_score="raise",
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        search.fit(
            train_frame[feature_columns],
            train_frame["target_cpi_inflation"],
        )
    convergence_count = sum("converge" in str(item.message).lower() for item in caught)
    if convergence_count:
        for item in caught:
            if "converge" in str(item.message).lower():
                warnings.warn(
                    f"{model_name} CV convergence warning: {item.message}",
                    category=item.category,
                    stacklevel=2,
                )
    best = search.best_params_
    if model_name == "elastic_net":
        best = {key.removeprefix("model__"): value for key, value in best.items()}
    return best, convergence_count


def _fit_tabular_model(
    model_name: str,
    params: dict[str, Any],
    train_frame: pd.DataFrame,
    feature_columns: list[str],
) -> Any:
    if model_name == "autoregression":
        model: Any = LinearRegression()
    elif model_name == "elastic_net":
        model = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "model",
                    ElasticNet(
                        max_iter=200_000,
                        tol=1e-5,
                        random_state=SEED,
                        **params,
                    ),
                ),
            ]
        )
    elif model_name == "random_forest":
        model = RandomForestRegressor(random_state=SEED, n_jobs=1, **params)
    elif model_name == "xgboost":
        model = XGBRegressor(
            random_state=SEED,
            objective="reg:squarederror",
            n_jobs=1,
            **params,
        )
    else:
        raise ValueError(f"Unsupported CPI model: {model_name}")
    model.fit(train_frame[feature_columns], train_frame["target_cpi_inflation"])
    if model_name == "elastic_net":
        fitted = model.named_steps["model"]
        if np.max(fitted.n_iter_) >= fitted.max_iter:
            raise RuntimeError("Elastic Net reached its iteration limit without convergence.")
    return model


def _available_training_rows(frame: pd.DataFrame, origin: pd.Timestamp) -> pd.DataFrame:
    """Select only supervised outcomes observed before the forecast-origin month."""
    return frame.loc[(frame["forecast_origin"] < origin) & (frame["target_date"] < origin)].copy()


def _sarimax_origin_forecast(
    frame: pd.DataFrame,
    origin_position: int,
    feature_columns: list[str],
    horizon: int,
) -> tuple[float, Any, dict[str, Any]]:
    """Fit SARIMAX on known target labels and forecast recursively to the origin+h row."""
    current = frame.iloc[origin_position]
    origin = pd.Timestamp(current["forecast_origin"])
    train = _available_training_rows(frame, origin)
    if len(train) < max(36, len(feature_columns) + 10):
        raise ValueError("Insufficient known CPI outcomes for SARIMAX at this origin.")

    scaler = StandardScaler()
    train_exog = scaler.fit_transform(train[feature_columns])
    latest_train_origin = pd.Timestamp(train["forecast_origin"].max())
    forecast_path = frame.loc[
        (frame["forecast_origin"] > latest_train_origin) & (frame["forecast_origin"] <= origin)
    ].copy()
    expected_steps = horizon + 1
    if len(forecast_path) != expected_steps:
        raise ValueError(
            "SARIMAX recursive forecast path does not match the horizon and origin calendar."
        )
    future_exog = scaler.transform(forecast_path[feature_columns])
    fitted = SARIMAX(
        train["target_cpi_inflation"].to_numpy(dtype=float),
        exog=train_exog,
        order=SARIMAX_ORDER,
        seasonal_order=SARIMAX_SEASONAL_ORDER,
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False, maxiter=150)
    converged = bool(fitted.mle_retvals.get("converged", False))
    if not converged:
        warnings.warn(
            f"SARIMAX did not converge for horizon {horizon} at origin {origin.date()}.",
            RuntimeWarning,
            stacklevel=2,
        )
    forecast = fitted.get_forecast(steps=expected_steps, exog=future_exog)
    value = float(np.asarray(forecast.predicted_mean)[-1])
    return (
        value,
        (scaler, fitted),
        {
            "sarimax_converged": converged,
            "sarimax_training_rows": len(train),
            "sarimax_forecast_steps": expected_steps,
        },
    )


def _persistence_forecast(frame: pd.DataFrame, origin: pd.Timestamp) -> float:
    known = frame.loc[
        (frame["target_date"] < origin) & (frame["forecast_origin"] < origin),
        "target_cpi_inflation",
    ]
    if known.empty:
        raise ValueError(f"No published CPI inflation is available before {origin.date()}.")
    return float(known.iloc[-1])


def run_configuration(
    frame: pd.DataFrame,
    configuration: str,
    horizon: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Tune on the initial training block and produce expanding-origin test forecasts."""
    feature_columns = [
        column
        for column in frame.columns
        if column.startswith(("cpi_lag_", "brent_", "fx_predicted_"))
        and column
        not in {
            "brent_usd_per_barrel_level",
            "brent_mom_pct_change",
            "brent_inr_proxy_level",
            "brent_inr_proxy_mom_pct_change",
        }
    ]
    if not feature_columns:
        raise ValueError(f"No predictor columns configured for {configuration}.")
    train_indices, validation_indices, test_indices = split_train_validation_test(frame)
    initial_train = frame.iloc[train_indices].copy()
    validation = frame.iloc[validation_indices].copy()
    test = frame.iloc[test_indices].copy()
    first_validation_origin = validation["forecast_origin"].iloc[0]
    tuning_train = initial_train.loc[initial_train["target_date"] < first_validation_origin].copy()
    if len(tuning_train) < 45:
        raise ValueError("The purged tuning training sample is too small.")

    fitted_parameters: dict[str, dict[str, Any]] = {}
    convergence_counts: dict[str, int] = {}
    for model_name in ML_MODELS:
        parameters, warning_count = _tune_model(
            model_name,
            tuning_train,
            feature_columns,
        )
        fitted_parameters[model_name] = parameters
        convergence_counts[model_name] = warning_count

    predictions: list[dict[str, Any]] = []
    last_artifacts: dict[str, Any] = {}
    sarimax_status: list[bool] = []
    for position in test_indices:
        row = frame.iloc[position]
        origin = pd.Timestamp(row["forecast_origin"])
        train = _available_training_rows(frame, origin)
        if len(train) < max(36, len(feature_columns) + 10):
            raise ValueError(f"Insufficient pre-origin training rows at {origin.date()}.")

        for model_name in ("autoregression", *ML_MODELS):
            model = _fit_tabular_model(
                model_name,
                fitted_parameters.get(model_name, {}),
                train,
                feature_columns,
            )
            predicted = float(model.predict(frame.loc[[position], feature_columns])[0])
            last_artifacts[model_name] = model
            predictions.append(_prediction_row(configuration, model_name, horizon, row, predicted))

        sarimax_predicted, sarimax_artifact, sarimax_meta = _sarimax_origin_forecast(
            frame,
            position,
            feature_columns,
            horizon,
        )
        last_artifacts["sarimax"] = sarimax_artifact
        sarimax_status.append(sarimax_meta["sarimax_converged"])
        predictions.append(
            _prediction_row(configuration, "sarimax", horizon, row, sarimax_predicted)
        )

        if configuration == "C0":
            predicted = _persistence_forecast(frame, origin)
            predictions.append(
                _prediction_row(configuration, "cpi_persistence", horizon, row, predicted)
            )

    metadata = {
        "configuration": configuration,
        "horizon": horizon,
        "feature_columns": feature_columns,
        "initial_train_rows": len(initial_train),
        "tuning_train_rows": len(tuning_train),
        "validation_rows": len(validation),
        "test_origins": len(test),
        "test_origin_start": test["forecast_origin"].min().date().isoformat(),
        "test_origin_end": test["forecast_origin"].max().date().isoformat(),
        "test_target_start": test["target_date"].min().date().isoformat(),
        "test_target_end": test["target_date"].max().date().isoformat(),
        "final_test_used_for_tuning": False,
        "hyperparameters": fitted_parameters,
        "elastic_net_cv_convergence_warnings": convergence_counts.get("elastic_net", 0),
        "sarimax_order": SARIMAX_ORDER,
        "sarimax_seasonal_order": SARIMAX_SEASONAL_ORDER,
        "sarimax_converged_origins": int(sum(sarimax_status)),
        "sarimax_total_origins": len(sarimax_status),
    }
    for model_name, artifact in last_artifacts.items():
        path = MODEL_ROOT / f"{configuration.lower()}_{model_name}_{horizon}m.pkl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as handle:
            pickle.dump(artifact, handle)
    return pd.DataFrame(predictions), metadata


def _prediction_row(
    configuration: str,
    model: str,
    horizon: int,
    row: pd.Series,
    predicted: float,
) -> dict[str, Any]:
    actual = float(row["target_cpi_inflation"])
    return {
        "configuration": configuration,
        "model": model,
        "forecast_origin": pd.Timestamp(row["forecast_origin"]),
        "target_date": pd.Timestamp(row["target_date"]),
        "horizon": horizon,
        "origin_cpi_inflation": float(row["origin_cpi_inflation"]),
        "actual": actual,
        "predicted": predicted,
        "error": predicted - actual,
        "fx_forecast_provenance": row.get("fx_forecast_provenance", ""),
    }


def run_inflation_experiments(
    frames: dict[tuple[str, int], pd.DataFrame],
    feature_coverage: dict[str, Any],
    target_thresholds: dict[int, float],
    brent_diagnostics: pd.DataFrame,
    brent_thresholds: dict[int, float],
    run_metadata: dict[str, Any],
) -> dict[str, pd.DataFrame | dict[str, Any]]:
    """Run all four information sets, horizons, model families, and diagnostics."""
    predictions: list[pd.DataFrame] = []
    model_metadata: dict[str, Any] = {}
    split_metadata: dict[str, Any] = {}
    for horizon in HORIZONS:
        keys = [
            frames[(configuration, horizon)]["forecast_origin"] for configuration in CONFIGURATIONS
        ]
        common_origins = keys[0]
        for dates in keys[1:]:
            common_origins = common_origins[common_origins.isin(dates)]
        if common_origins.empty:
            raise ValueError(f"No common forecast origins across C0-C3 at horizon {horizon}.")
        for configuration in CONFIGURATIONS:
            frame = frames[(configuration, horizon)]
            frame = frame.loc[frame["forecast_origin"].isin(common_origins)].reset_index(drop=True)
            output, metadata = run_configuration(frame, configuration, horizon)
            predictions.append(output)
            model_metadata[f"{configuration}_{horizon}m"] = metadata
            split_metadata[f"{horizon}m"] = {
                key: metadata[key]
                for key in (
                    "initial_train_rows",
                    "tuning_train_rows",
                    "validation_rows",
                    "test_origins",
                    "test_origin_start",
                    "test_origin_end",
                    "test_target_start",
                    "test_target_end",
                )
            }

    prediction_frame = pd.concat(predictions, ignore_index=True)
    for (horizon, model), group in prediction_frame.groupby(["horizon", "model"]):
        if model == "cpi_persistence":
            continue
        target_sets = group.groupby("configuration")["target_date"].apply(
            lambda values: tuple(values.astype(str))
        )
        if target_sets.nunique() != 1:
            raise ValueError(
                f"Configurations do not share forecast targets for {model}, {horizon}M."
            )

    comparison = build_model_comparison(prediction_frame)
    incremental = build_incremental_comparison(prediction_frame)
    residuals = build_residual_diagnostics(prediction_frame)
    high_inflation = build_episode_error_summary(
        prediction_frame,
        target_thresholds,
        "high_inflation",
    )
    oil_spikes = build_episode_error_summary(
        prediction_frame,
        target_thresholds,
        "brent_spike",
        episode_values=brent_diagnostics,
        value_thresholds=brent_thresholds,
    )
    early_late = _build_window_comparison(prediction_frame)
    run_metadata.update(
        {
            "model_metadata": model_metadata,
            "split_metadata": split_metadata,
            "feature_coverage": feature_coverage,
            "target_high_inflation_thresholds": target_thresholds,
            "training_brent_spike_thresholds": brent_thresholds,
            "statistical_significance_tests": "No Diebold-Mariano test conducted.",
            "prediction_intervals": "Not implemented.",
        }
    )
    return {
        "predictions": prediction_frame,
        "comparison": comparison,
        "incremental": incremental,
        "residuals": residuals,
        "high_inflation": high_inflation,
        "oil_spikes": oil_spikes,
        "early_late": early_late,
        "metadata": run_metadata,
    }


def _build_window_comparison(predictions: pd.DataFrame) -> pd.DataFrame:
    """Compare chronological first/second halves of the final test window."""
    rows: list[dict[str, Any]] = []
    for (horizon, configuration, model), group in predictions.groupby(
        ["horizon", "configuration", "model"], sort=True
    ):
        ordered = group.sort_values("target_date").reset_index(drop=True)
        midpoint = len(ordered) // 2
        for window, subset in (
            ("early", ordered.iloc[:midpoint]),
            ("late", ordered.iloc[midpoint:]),
        ):
            if subset.empty:
                continue
            error = subset["error"].to_numpy(dtype=float)
            rows.append(
                {
                    "horizon": horizon,
                    "configuration": configuration,
                    "model": model,
                    "window": window,
                    "n": len(subset),
                    "target_start": subset["target_date"].min().date().isoformat(),
                    "target_end": subset["target_date"].max().date().isoformat(),
                    "mae": float(np.mean(np.abs(error))),
                    "rmse": float(np.sqrt(np.mean(error**2))),
                    "bias": float(np.mean(error)),
                    "interpretation_note": (
                        "descriptive split of final test, not separate validation"
                    ),
                }
            )
    return pd.DataFrame(rows)
