"""Constrained classifier candidates and leakage-safe expanding validation."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier


@dataclass(frozen=True)
class Candidate:
    """A prespecified model configuration."""

    model: str
    parameters: dict[str, Any]

    @property
    def candidate_id(self) -> str:
        return "_".join(f"{key}-{self.parameters[key]}" for key in sorted(self.parameters))


def candidate_grid() -> dict[str, list[Candidate]]:
    """Return small grids fixed before looking at final-test outcomes."""
    return {
        "logistic_regression": [
            Candidate(
                "logistic_regression",
                {
                    "C": c,
                    "class_weight": weight,
                    "solver": "lbfgs",
                    "max_iter": 5000,
                },
            )
            for c in (0.1, 1.0, 10.0)
            for weight in (None, "balanced")
        ],
        "random_forest": [
            Candidate(
                "random_forest",
                {
                    "n_estimators": 300,
                    "max_depth": depth,
                    "min_samples_leaf": 5,
                    "max_features": "sqrt",
                    "class_weight": weight,
                },
            )
            for depth in (2, 3)
            for weight in (None, "balanced_subsample")
        ],
        "xgboost": [
            Candidate(
                "xgboost",
                {
                    "n_estimators": 100,
                    "max_depth": depth,
                    "learning_rate": 0.03,
                    "min_child_weight": 5,
                    "subsample": 0.8,
                    "colsample_bytree": 0.8,
                    "reg_lambda": 10.0,
                    "gamma": 0.0,
                },
            )
            for depth in (1, 2)
        ],
    }


def fit_candidate(
    candidate: Candidate,
    features: list[str],
    x_train: pd.DataFrame,
    y_train: pd.Series,
    seed: int,
) -> Any:
    """Fit one candidate, deriving all class balancing from this training fold."""
    if y_train.nunique() != 2:
        raise ValueError("Every training fold must contain both elevated and non-elevated labels.")
    parameters = candidate.parameters
    if candidate.model == "logistic_regression":
        estimator: Any = Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        C=float(parameters["C"]),
                        class_weight=parameters["class_weight"],
                        solver=str(parameters["solver"]),
                        max_iter=int(parameters["max_iter"]),
                        random_state=seed,
                    ),
                ),
            ]
        )
    elif candidate.model == "random_forest":
        estimator = RandomForestClassifier(
            n_estimators=int(parameters["n_estimators"]),
            max_depth=int(parameters["max_depth"]),
            min_samples_leaf=int(parameters["min_samples_leaf"]),
            max_features=str(parameters["max_features"]),
            class_weight=parameters["class_weight"],
            random_state=seed,
            n_jobs=1,
        )
    elif candidate.model == "xgboost":
        positives = int(y_train.sum())
        negatives = int(len(y_train) - positives)
        estimator = XGBClassifier(
            n_estimators=int(parameters["n_estimators"]),
            max_depth=int(parameters["max_depth"]),
            learning_rate=float(parameters["learning_rate"]),
            min_child_weight=int(parameters["min_child_weight"]),
            subsample=float(parameters["subsample"]),
            colsample_bytree=float(parameters["colsample_bytree"]),
            reg_lambda=float(parameters["reg_lambda"]),
            gamma=float(parameters["gamma"]),
            scale_pos_weight=negatives / positives,
            objective="binary:logistic",
            eval_metric="logloss",
            tree_method="hist",
            random_state=seed,
            n_jobs=1,
            verbosity=0,
        )
    else:
        raise ValueError(f"Unknown classifier {candidate.model}.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            estimator.fit(x_train[features], y_train)
    except ConvergenceWarning as exc:
        raise RuntimeError(f"{candidate.model} did not converge: {exc}") from exc
    return estimator


def predict_candidate(
    candidate: Candidate,
    features: list[str],
    frame: pd.DataFrame,
    seed: int,
) -> pd.DataFrame:
    """Generate validation-only expanding-origin predictions for a fixed candidate."""
    scored = frame.loc[
        (frame["target_month"] >= frame.attrs["validation_start"])
        & (frame["target_month"] <= pd.Timestamp("2022-12-01"))
    ].sort_values("forecast_origin")
    rows: list[dict[str, Any]] = []
    for row in scored.itertuples(index=False):
        origin = row.forecast_origin
        training = frame.loc[frame["target_month"] < origin].sort_values("forecast_origin")
        if training.empty or training["elevated_target"].nunique() != 2:
            raise ValueError(f"Insufficient mature training labels at validation origin {origin}.")
        estimator = fit_candidate(
            candidate,
            features,
            training,
            training["elevated_target"].astype(int),
            seed,
        )
        probability = float(
            estimator.predict_proba(pd.DataFrame([row._asdict()])[features])[0, 1]
        )
        rows.append(
            {
                "forecast_origin": origin,
                "target_month": row.target_month,
                "actual": int(row.elevated_target),
                "probability": probability,
                "validation_training_n": len(training),
                "validation_training_positive": int(training["elevated_target"].sum()),
            }
        )
    return pd.DataFrame(rows)


def validation_frame(frame: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Attach the first validation target month for the direct forecast horizon."""
    result = frame.copy()
    result.attrs["validation_start"] = pd.Timestamp("2021-01-01") + pd.DateOffset(
        months=horizon
    )
    return result
