"""Leakage-aware Stage 1 forecasting for monthly USD/INR levels."""

from __future__ import annotations

import json
import pickle
import platform
import warnings
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNet
from sklearn.metrics import r2_score
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parents[3]
EXCHANGE_DATA = ROOT / "data" / "processed" / "features" / "research_master_feature_panel.csv"
ARTIFACTS_ROOT = ROOT / "artifacts"
PREDICTIONS_ROOT = ARTIFACTS_ROOT / "predictions" / "exchange_rate"
MODELS_ROOT = ARTIFACTS_ROOT / "models" / "exchange_rate"
METRICS_ROOT = ARTIFACTS_ROOT / "metrics" / "exchange_rate"
REPORT_ROOT = ROOT / "reports" / "experiments"

HORIZONS = (1, 3, 6)
SEED = 42
LAGS = (1, 2, 3, 6, 12)
EXCHANGE_FEATURES = (
    "usd_inr_monthly",
    "usd_inr_mom_change",
    "usd_inr_mom_pct_change",
    "usd_inr_log_change",
    "usd_inr_depreciation_log_change",
    "usd_inr_appreciation_log_change",
)
MACRO_FEATURES = (
    "brent_usd_per_barrel_level",
    "brent_mom_pct_change",
    "brent_inr_proxy_level",
    "brent_inr_proxy_mom_pct_change",
    "repo_rate_level",
    "repo_rate_change_pp",
    "Trade_NEER_level",
    "Trade_NEER_mom_pct_change",
    "Trade_REER_level",
    "Trade_REER_mom_pct_change",
)
FEATURE_COLUMNS = tuple(
    [f"{name}_lag_{lag}" for name in EXCHANGE_FEATURES for lag in (0, *LAGS)]
    + [f"{name}_lag_{lag}" for name in MACRO_FEATURES for lag in LAGS]
)
ARIMA_ORDERS = (
    (0, 0, 0),
    (1, 0, 0),
    (2, 0, 0),
    (1, 1, 0),
    (0, 1, 1),
    (1, 1, 1),
    (2, 1, 0),
)


def load_stage1_dataset() -> pd.DataFrame:
    """Load the verified master feature panel and validate monthly date integrity."""
    panel = pd.read_csv(EXCHANGE_DATA)
    panel["date"] = pd.to_datetime(panel["date"], errors="coerce")
    panel = panel.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if panel["date"].duplicated().any():
        raise ValueError("The Stage 1 source panel contains duplicate dates.")
    periods = panel["date"].dt.to_period("M")
    if periods.duplicated().any():
        raise ValueError("The Stage 1 source panel contains more than one observation per month.")
    if not periods.is_monotonic_increasing:
        raise ValueError("The Stage 1 source panel must be chronologically ordered.")
    expected_periods = pd.period_range(periods.iloc[0], periods.iloc[-1], freq="M")
    if not periods.reset_index(drop=True).equals(pd.Series(expected_periods)):
        raise ValueError(
            "The Stage 1 source panel has missing months; row-based lags are not valid."
        )

    numeric_columns = (*EXCHANGE_FEATURES, *MACRO_FEATURES)
    for column in numeric_columns:
        if column in panel.columns:
            panel[column] = pd.to_numeric(panel[column], errors="coerce")
    return panel


def build_horizon_frame(panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Align the target by calendar month and create lagged origin-time predictors."""
    if horizon not in HORIZONS:
        raise ValueError(f"Unsupported forecast horizon: {horizon}")
    frame = panel.copy().sort_values("date").reset_index(drop=True)
    frame["date"] = pd.to_datetime(frame["date"])
    periods = frame["date"].dt.to_period("M")
    if frame["date"].duplicated().any() or periods.duplicated().any():
        raise ValueError("The source panel must have one observation per month.")
    expected_periods = pd.period_range(periods.iloc[0], periods.iloc[-1], freq="M")
    if not periods.reset_index(drop=True).equals(pd.Series(expected_periods)):
        raise ValueError("The source panel must contain a complete monthly calendar.")

    period_to_value = pd.Series(
        frame["usd_inr_monthly"].to_numpy(),
        index=periods,
    )
    target_periods = periods + horizon
    frame["forecast_origin"] = frame["date"]
    frame["target_date"] = target_periods.dt.to_timestamp()
    frame["target_level"] = target_periods.map(period_to_value)

    for name in EXCHANGE_FEATURES:
        if name not in frame.columns:
            continue
        frame[f"{name}_lag_0"] = frame[name]
        for lag in LAGS:
            frame[f"{name}_lag_{lag}"] = frame[name].shift(lag)
    for name in MACRO_FEATURES:
        if name not in frame.columns:
            continue
        for lag in LAGS:
            frame[f"{name}_lag_{lag}"] = frame[name].shift(lag)

    feature_columns = [column for column in FEATURE_COLUMNS if column in frame.columns]
    required_columns = ["target_level", *feature_columns]
    frame = frame.dropna(subset=required_columns).reset_index(drop=True)
    if frame.empty:
        raise ValueError("No complete Stage 1 observations remain after feature alignment.")
    return frame


def split_train_validation_test(
    frame: pd.DataFrame,
) -> tuple[pd.Index, pd.Index, pd.Index]:
    """Return contiguous 70/15/15 chronological index blocks."""
    n_obs = len(frame)
    if n_obs < 20:
        raise ValueError(f"At least 20 eligible observations are required; received {n_obs}.")
    train_end = int(n_obs * 0.70)
    validation_end = int(n_obs * 0.85)
    return (
        pd.Index(range(train_end)),
        pd.Index(range(train_end, validation_end)),
        pd.Index(range(validation_end, n_obs)),
    )


def random_walk_forecast(
    available_history: pd.DataFrame,
    origin: pd.Timestamp,
    horizon: int,
) -> float:
    """Forecast the future level as the latest exchange-rate level known at origin."""
    if horizon not in HORIZONS:
        raise ValueError(f"Unsupported forecast horizon: {horizon}")
    history = available_history.loc[available_history["date"] <= origin, "usd_inr_monthly"]
    if history.empty:
        raise ValueError(f"No exchange-rate observation is available by origin {origin}.")
    return float(history.iloc[-1])


def _make_feature_matrix(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    columns = [column for column in FEATURE_COLUMNS if column in frame.columns]
    if not columns:
        raise ValueError("No configured Stage 1 predictors are present.")
    return frame[columns].copy(), frame["target_level"].copy()


def evaluate_predictions(
    actual: np.ndarray,
    predicted: np.ndarray,
    origin_values: np.ndarray | None = None,
) -> dict[str, float]:
    """Calculate level errors and direction accuracy relative to each forecast origin."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if actual.ndim != 1 or predicted.ndim != 1 or actual.shape != predicted.shape:
        raise ValueError(
            "Actual and predicted values must be one-dimensional arrays of equal length."
        )
    if actual.size == 0 or not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("Actual and predicted values must be non-empty and finite.")
    error = predicted - actual
    mape = (
        float(np.mean(np.abs(error / actual)) * 100.0)
        if np.all(actual != 0)
        else float("nan")
    )
    if origin_values is None:
        directional_accuracy = float("nan")
    else:
        origins = np.asarray(origin_values, dtype=float)
        if origins.shape != actual.shape or not np.isfinite(origins).all():
            raise ValueError("Origin values must be finite and match the actual-value shape.")
        directional_accuracy = float(
            np.mean(np.sign(predicted - origins) == np.sign(actual - origins))
        )
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(np.square(error)))),
        "mape": mape,
        "r2": float(r2_score(actual, predicted)) if np.unique(actual).size > 1 else float("nan"),
        "directional_accuracy": directional_accuracy,
        "bias": float(np.mean(error)),
    }


def _purged_cv_splits(
    frame: pd.DataFrame,
    n_splits: int = 3,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Create expanding folds whose training labels predate each validation origin."""
    splitter = TimeSeriesSplit(n_splits=n_splits)
    splits: list[tuple[np.ndarray, np.ndarray]] = []
    for candidate_train, validation in splitter.split(frame):
        first_validation_origin = frame.iloc[validation[0]]["forecast_origin"]
        purged_train = candidate_train[
            frame.iloc[candidate_train]["target_date"].to_numpy()
            < np.datetime64(first_validation_origin)
        ]
        if purged_train.size == 0:
            raise ValueError("Purging horizon-overlapping targets left an empty CV training fold.")
        splits.append((purged_train, validation))
    return splits


def _select_model_hyperparameters(
    estimator: Any,
    param_grid: dict[str, list[Any]],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    train_frame: pd.DataFrame,
) -> tuple[dict[str, Any], int]:
    """Tune on purged expanding folds within the training partition only."""
    splits = _purged_cv_splits(train_frame)
    grid_params = (
        {f"model__{key}": values for key, values in param_grid.items()}
        if isinstance(estimator, Pipeline)
        else param_grid
    )
    search = GridSearchCV(
        estimator,
        param_grid=grid_params,
        cv=splits,
        scoring="neg_root_mean_squared_error",
        n_jobs=1,
        error_score="raise",
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        search.fit(X_train, y_train)
    warning_count = sum(issubclass(item.category, ConvergenceWarning) for item in caught)
    best_params = search.best_params_
    if isinstance(estimator, Pipeline):
        best_params = {key.removeprefix("model__"): value for key, value in best_params.items()}
    return best_params, warning_count


def _select_arima_order(train_series: pd.Series) -> tuple[int, int, int]:
    """Select an ARIMA order by AIC using the training partition only."""
    best_order: tuple[int, int, int] | None = None
    best_aic = np.inf
    for order in ARIMA_ORDERS:
        model = ARIMA(
            train_series.astype(float),
            order=order,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fitted = model.fit()
        if np.isfinite(fitted.aic) and fitted.aic < best_aic:
            best_order = order
            best_aic = float(fitted.aic)
    if best_order is None:
        raise ValueError("No candidate ARIMA model produced a finite training AIC.")
    return best_order


def _fit_final_estimator(
    model_name: str,
    params: dict[str, Any],
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> Any:
    """Fit the selected estimator on the permitted pre-test training sample."""
    if model_name == "elastic_net":
        model: Any = Pipeline(
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
        raise ValueError(f"Unsupported estimator: {model_name}")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        model.fit(X_train, y_train)
    convergence_warnings = [
        item for item in caught if issubclass(item.category, ConvergenceWarning)
    ]
    if convergence_warnings:
        messages = "; ".join(str(item.message) for item in convergence_warnings)
        raise RuntimeError(f"{model_name} final fit did not converge: {messages}")
    return model


def _save_pickle(path: Path, object_to_store: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(object_to_store, handle)


def _save_arima_specification(
    path: Path,
    fitted_model: Any,
    order: tuple[int, int, int],
    fit_end: pd.Timestamp,
) -> None:
    """Persist a canonical, reconstructable ARIMA specification and parameter vector."""
    artifact = {
        "model": "ARIMA",
        "order": order,
        "target": "usd_inr_monthly",
        "fit_end": fit_end.date().isoformat(),
        "observations": int(fitted_model.nobs),
        "parameter_names": list(fitted_model.param_names),
        "parameters_rounded_12dp": [
            round(float(value), 12) for value in fitted_model.params
        ],
        "selection": "AIC on the initial training partition only",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(artifact, handle, indent=2)


def _prediction_frame(
    model_name: str,
    horizon: int,
    test_frame: pd.DataFrame,
    predicted: np.ndarray,
) -> pd.DataFrame:
    actual = test_frame["target_level"].to_numpy(dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return pd.DataFrame(
        {
            "model": model_name,
            "forecast_origin": test_frame["forecast_origin"].to_numpy(),
            "target_date": test_frame["target_date"].to_numpy(),
            "horizon": horizon,
            "origin_value": test_frame["usd_inr_monthly"].to_numpy(dtype=float),
            "actual": actual,
            "predicted": predicted,
            "error": predicted - actual,
        }
    )


def train_and_predict_model(
    frame: pd.DataFrame,
    model_name: str,
    horizon: int,
    panel: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Tune on training data, refit before the holdout, and evaluate fixed test origins."""
    train_idx, validation_idx, test_idx = split_train_validation_test(frame)
    initial_train = frame.iloc[train_idx].copy()
    validation_frame = frame.iloc[validation_idx].copy()
    test_frame = frame.iloc[test_idx].copy()
    if test_frame.empty:
        raise ValueError(f"No test observations remain for horizon {horizon}.")
    first_test_origin = test_frame["forecast_origin"].iloc[0]
    pretest_frame = frame.iloc[np.concatenate([train_idx, validation_idx])].copy()
    final_train_frame = pretest_frame.loc[
        pretest_frame["target_date"] < first_test_origin
    ].copy()
    if final_train_frame.empty:
        raise ValueError("No pre-test training labels remain after horizon purging.")

    origin_values = test_frame["usd_inr_monthly"].to_numpy(dtype=float)
    if model_name == "random_walk":
        predicted = np.asarray(
            [
                random_walk_forecast(panel, origin, horizon)
                for origin in test_frame["forecast_origin"]
            ],
            dtype=float,
        )
        estimator = None
        metadata: dict[str, Any] = {}
    elif model_name == "arima":
        order = _select_arima_order(initial_train["usd_inr_monthly"])
        predicted_values: list[float] = []
        estimator = None
        last_origin = pd.Timestamp(test_frame["forecast_origin"].iloc[-1])
        for origin in test_frame["forecast_origin"]:
            history = panel.loc[panel["date"] <= origin, "usd_inr_monthly"].astype(float)
            fitted = ARIMA(
                history,
                order=order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit()
            predicted_values.append(float(fitted.forecast(steps=horizon).iloc[-1]))
            estimator = fitted
        predicted = np.asarray(predicted_values, dtype=float)
        metadata = {
            "order": order,
            "prediction_strategy": "refit at each origin; direct h-step forecast",
        }
        if estimator is not None:
            _save_arima_specification(
                MODELS_ROOT / f"arima_{horizon}m.json",
                estimator,
                order,
                last_origin,
            )
    else:
        X_initial, y_initial = _make_feature_matrix(initial_train)
        params_grid: dict[str, list[Any]]
        if model_name == "elastic_net":
            params_grid = {
                "alpha": [0.01, 0.1, 1.0],
                "l1_ratio": [0.1, 0.5, 0.9],
            }
            base_estimator = Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "model",
                        ElasticNet(max_iter=200_000, tol=1e-5, random_state=SEED),
                    ),
                ]
            )
        elif model_name == "random_forest":
            params_grid = {
                "n_estimators": [200, 400],
                "max_depth": [None, 5, 8],
                "min_samples_leaf": [1, 2],
            }
            base_estimator = RandomForestRegressor(random_state=SEED, n_jobs=1)
        elif model_name == "xgboost":
            params_grid = {
                "n_estimators": [200, 400],
                "max_depth": [2, 3, 5],
                "learning_rate": [0.03, 0.06],
                "subsample": [0.8, 1.0],
            }
            base_estimator = XGBRegressor(
                random_state=SEED,
                objective="reg:squarederror",
                n_jobs=1,
            )
        else:
            raise ValueError(f"Unsupported model name: {model_name}")

        params, tuning_convergence_warnings = _select_model_hyperparameters(
            base_estimator,
            params_grid,
            X_initial,
            y_initial,
            initial_train,
        )
        X_final, y_final = _make_feature_matrix(final_train_frame)
        estimator = _fit_final_estimator(model_name, params, X_final, y_final)
        X_test, _ = _make_feature_matrix(test_frame)
        predicted = estimator.predict(X_test)
        metadata = {
            "params": params,
            "tuning_convergence_warning_count": tuning_convergence_warnings,
        }
        _save_pickle(MODELS_ROOT / f"{model_name}_{horizon}m.pkl", estimator)

    predictions = _prediction_frame(model_name, horizon, test_frame, predicted)
    metrics = evaluate_predictions(
        predictions["actual"].to_numpy(),
        predictions["predicted"].to_numpy(),
        origin_values,
    )
    return predictions, {
        "metrics": metrics,
        "metadata": metadata,
        "split": {
            "initial_train_rows": len(initial_train),
            "validation_rows": len(validation_frame),
            "final_train_rows": len(final_train_frame),
            "test_rows": len(test_frame),
            "final_train_label_end": str(final_train_frame["target_date"].max().date()),
            "first_test_origin": str(first_test_origin.date()),
            "test_origin_start": str(test_frame["forecast_origin"].min().date()),
            "test_origin_end": str(test_frame["forecast_origin"].max().date()),
            "test_target_start": str(test_frame["target_date"].min().date()),
            "test_target_end": str(test_frame["target_date"].max().date()),
        },
    }


def run_stage1_forecasting() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Run the leakage-audited USD/INR forecasting comparison at all horizons."""
    panel = load_stage1_dataset()
    model_names = ("random_walk", "arima", "elastic_net", "random_forest", "xgboost")
    prediction_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    run_metadata: dict[str, Any] = {
        "seed": SEED,
        "horizons_months": HORIZONS,
        "target": "usd_inr_monthly level at forecast origin + horizon",
        "forecasting_strategy": {
            "machine_learning": "direct horizon target; fixed pre-test fit; origin-time predictors",
            "arima": (
                "training-only AIC order selection; refit through each origin; "
                "direct horizon forecast"
            ),
            "random_walk": "latest USD/INR level available at forecast origin",
        },
        "exchange_rate_feature_lags_months": (0, *LAGS),
        "macro_feature_lags_months": LAGS,
        "feature_columns": FEATURE_COLUMNS,
        "model_search_spaces": {
            "elastic_net": {"alpha": [0.01, 0.1, 1.0], "l1_ratio": [0.1, 0.5, 0.9]},
            "random_forest": {
                "n_estimators": [200, 400],
                "max_depth": [None, 5, 8],
                "min_samples_leaf": [1, 2],
            },
            "xgboost": {
                "n_estimators": [200, 400],
                "max_depth": [2, 3, 5],
                "learning_rate": [0.03, 0.06],
                "subsample": [0.8, 1.0],
            },
            "arima_orders": ARIMA_ORDERS,
        },
        "validation": {
            "outer_split": [0.70, 0.15, 0.15],
            "hyperparameter_cv": "3-fold expanding TimeSeriesSplit with target-date purging",
            "test_period_used_for_tuning": False,
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": version("numpy"),
            "pandas": version("pandas"),
            "scikit_learn": version("scikit-learn"),
            "statsmodels": version("statsmodels"),
            "xgboost": version("xgboost"),
        },
        "model_metadata": {},
        "split_metadata": {},
        "panel_date_range": [
            str(panel["date"].min().date()),
            str(panel["date"].max().date()),
        ],
    }

    for horizon in HORIZONS:
        horizon_frame = build_horizon_frame(panel, horizon)
        for model_name in model_names:
            predictions, result = train_and_predict_model(
                horizon_frame,
                model_name,
                horizon,
                panel,
            )
            prediction_frames.append(predictions)
            metric_rows.append(
                {
                    "horizon": horizon,
                    "model": model_name,
                    "n": len(predictions),
                    "test_target_start": predictions["target_date"].min().date().isoformat(),
                    "test_target_end": predictions["target_date"].max().date().isoformat(),
                    **result["metrics"],
                }
            )
            run_metadata["model_metadata"][f"{model_name}_{horizon}m"] = result["metadata"]
            run_metadata["split_metadata"][f"{horizon}m"] = result["split"]

    predictions = pd.concat(prediction_frames, ignore_index=True)
    metrics = pd.DataFrame(metric_rows)
    for horizon, horizon_results in predictions.groupby("horizon"):
        expected = horizon_results.groupby("model")["target_date"].apply(
            lambda values: tuple(values.astype(str))
        )
        if expected.nunique() != 1:
            raise ValueError(
                f"Models do not share identical test target dates at horizon {horizon}."
            )

    PREDICTIONS_ROOT.mkdir(parents=True, exist_ok=True)
    MODELS_ROOT.mkdir(parents=True, exist_ok=True)
    METRICS_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(REPORT_ROOT / "EXCHANGE_RATE_FORECAST_PREDICTIONS.csv", index=False)
    predictions.to_csv(PREDICTIONS_ROOT / "stage1_exchange_rate_predictions.csv", index=False)
    metrics.to_csv(REPORT_ROOT / "EXCHANGE_RATE_MODEL_COMPARISON.csv", index=False)
    metrics.to_csv(METRICS_ROOT / "stage1_exchange_rate_metrics.csv", index=False)
    metadata_path = ARTIFACTS_ROOT / "exchange_rate_model_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(run_metadata, handle, indent=2, default=str)
    return predictions, metrics, run_metadata
