"""Parsimonious symmetric and asymmetric distributed-lag model construction."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Literal

import numpy as np
import pandas as pd
import statsmodels.api as sm

ModelKind = Literal["symmetric", "asymmetric", "proxy"]
ControlKind = Literal["none", "brent", "brent_interactions", "proxy"]
MAX_OUTCOME_LAG = 3
MAX_FX_LAG = 6
PRIMARY_MAX_FX_LAG = 3
MIN_OBSERVATIONS_PER_PARAMETER = 7.5


@dataclass(frozen=True)
class ModelDesign:
    """Outcome and ordered regressor matrix for one declared specification."""

    outcome: pd.Series
    regressors: pd.DataFrame
    dates: pd.Series
    feature_names: tuple[str, ...]


def build_analysis_panel(panel: pd.DataFrame, outcome: str) -> pd.DataFrame:
    """Create backward lags while retaining one common maximum-lag sample."""
    required = {"date", outcome, "fx_log_change_pct", "depreciation", "appreciation"}
    missing = required.difference(panel.columns)
    if missing:
        raise ValueError(f"Analysis panel is missing required fields: {sorted(missing)}")
    frame = panel[["date", outcome, "fx_log_change_pct", "depreciation", "appreciation"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame = frame.sort_values("date").reset_index(drop=True)
    frame = frame.rename(columns={outcome: "outcome"})
    frame["date_period"] = frame["date"].dt.to_period("M")
    if frame["date_period"].duplicated().any():
        raise ValueError("Model input has duplicate monthly dates.")
    expected = pd.period_range(
        frame["date_period"].iloc[0], frame["date_period"].iloc[-1], freq="M"
    )
    if not frame["date_period"].reset_index(drop=True).equals(pd.Series(expected)):
        raise ValueError("Model input must have a complete monthly calendar.")

    for lag in range(1, MAX_OUTCOME_LAG + 1):
        frame[f"outcome_lag_{lag}"] = frame["outcome"].shift(lag)
    for lag in range(MAX_FX_LAG + 1):
        frame[f"fx_lag_{lag}"] = frame["fx_log_change_pct"].shift(lag)
        frame[f"depreciation_lag_{lag}"] = frame["depreciation"].shift(lag)
        frame[f"appreciation_lag_{lag}"] = frame["appreciation"].shift(lag)
    if "brent_log_change_pct" in panel:
        frame["brent_lag_1"] = pd.to_numeric(panel["brent_log_change_pct"], errors="coerce").shift(
            1
        )
    if "brent_inr_proxy_log_change_pct" in panel:
        frame["proxy_lag_1"] = pd.to_numeric(
            panel["brent_inr_proxy_log_change_pct"], errors="coerce"
        ).shift(1)
    if "repo_change_pp" in panel:
        frame["repo_lag_1"] = pd.to_numeric(panel["repo_change_pp"], errors="coerce").shift(1)
    for name in ("trade_neer", "trade_reer", "export_neer", "export_reer"):
        column = f"{name}_log_change_pct"
        if column in panel:
            frame[f"{name}_lag_1"] = pd.to_numeric(panel[column], errors="coerce").shift(1)

    required_core = [
        "outcome",
        *(f"outcome_lag_{lag}" for lag in range(1, MAX_OUTCOME_LAG + 1)),
        *(f"fx_lag_{lag}" for lag in range(MAX_FX_LAG + 1)),
        *(f"depreciation_lag_{lag}" for lag in range(MAX_FX_LAG + 1)),
        *(f"appreciation_lag_{lag}" for lag in range(MAX_FX_LAG + 1)),
    ]
    frame = frame.dropna(subset=required_core).reset_index(drop=True)
    return frame


def build_model_design(
    frame: pd.DataFrame,
    p: int,
    q: int,
    kind: ModelKind,
    control: ControlKind = "none",
    lag_only: bool = False,
    post_2020_break: bool = False,
) -> ModelDesign:
    """Build a model matrix with explicitly separated controls and FX terms."""
    if not 1 <= p <= MAX_OUTCOME_LAG:
        raise ValueError(f"Outcome lag p must be between 1 and {MAX_OUTCOME_LAG}.")
    if not 0 <= q <= MAX_FX_LAG:
        raise ValueError(f"FX lag q must be between 0 and {MAX_FX_LAG}.")
    if lag_only and q == 0:
        raise ValueError("A lag-only model requires an FX lag of at least one month.")
    if kind == "proxy" and control not in {"none", "proxy"}:
        raise ValueError("The proxy-only alternative cannot be combined with another control.")
    if kind != "proxy" and control == "proxy":
        raise ValueError("The Brent-INR proxy alternative is estimated separately from FX terms.")

    regressors: dict[str, pd.Series] = {"const": pd.Series(1.0, index=frame.index)}
    for lag in range(1, p + 1):
        regressors[f"outcome_lag_{lag}"] = frame[f"outcome_lag_{lag}"]

    lag_start = 1 if lag_only else 0
    if kind == "symmetric":
        for lag in range(lag_start, q + 1):
            regressors[f"fx_lag_{lag}"] = frame[f"fx_lag_{lag}"]
    elif kind == "asymmetric":
        for lag in range(lag_start, q + 1):
            regressors[f"depreciation_lag_{lag}"] = frame[f"depreciation_lag_{lag}"]
            regressors[f"appreciation_lag_{lag}"] = frame[f"appreciation_lag_{lag}"]
    elif kind == "proxy":
        if "proxy_lag_1" not in frame:
            raise ValueError("Brent-INR proxy change is unavailable in this model frame.")
        regressors["proxy_lag_1"] = frame["proxy_lag_1"]
    else:
        raise ValueError(f"Unsupported Stage 3 model kind: {kind}")

    if control in {"brent", "brent_interactions"}:
        if "brent_lag_1" not in frame:
            raise ValueError("Lagged Brent changes are unavailable in this model frame.")
        regressors["brent_lag_1"] = frame["brent_lag_1"]
        if control == "brent_interactions":
            if kind != "asymmetric":
                raise ValueError("FX-by-Brent interactions require an asymmetric FX specification.")
            regressors["depreciation_x_brent"] = frame["depreciation_lag_0"] * frame["brent_lag_1"]
            regressors["appreciation_x_brent"] = frame["appreciation_lag_0"] * frame["brent_lag_1"]

    if post_2020_break:
        dates = pd.to_datetime(frame["date"])
        post = dates.ge(pd.Timestamp("2020-03-01")).astype(float)
        regressors["post_2020"] = post
        if kind == "asymmetric":
            regressors["depreciation_x_post_2020"] = frame["depreciation_lag_0"] * post
            regressors["appreciation_x_post_2020"] = frame["appreciation_lag_0"] * post
        elif kind == "symmetric":
            regressors["fx_x_post_2020"] = frame["fx_lag_0"] * post

    design = pd.DataFrame(regressors, index=frame.index)
    outcome = pd.to_numeric(frame["outcome"], errors="coerce")
    valid = outcome.notna() & design.notna().all(axis=1)
    design = design.loc[valid].astype(float)
    outcome = outcome.loc[valid].astype(float)
    dates = pd.to_datetime(frame.loc[valid, "date"]).reset_index(drop=True)
    if not np.isfinite(design.to_numpy()).all() or not np.isfinite(outcome.to_numpy()).all():
        raise ValueError("Non-finite model values are not permitted.")
    if len(outcome) <= design.shape[1]:
        raise ValueError("Model has no residual degrees of freedom.")
    return ModelDesign(
        outcome=outcome.reset_index(drop=True),
        regressors=design.reset_index(drop=True),
        dates=dates,
        feature_names=tuple(design.columns),
    )


def choose_lags(
    analysis_frames: dict[str, pd.DataFrame],
    kind: ModelKind,
    control: ControlKind = "none",
    max_p: int = MAX_OUTCOME_LAG,
    max_q: int = PRIMARY_MAX_FX_LAG,
) -> tuple[int, int, pd.DataFrame]:
    """Select a shared p/q pair using summed BIC over primary CPI and WPI outcomes."""
    if len(analysis_frames) < 2:
        raise ValueError("Shared lag selection requires at least two comparable outcomes.")
    rows: list[dict[str, float | int | str]] = []
    for p, q in product(range(1, max_p + 1), range(0, max_q + 1)):
        outcome_bics: dict[str, float] = {}
        valid = True
        for name, frame in analysis_frames.items():
            design = build_model_design(frame, p, q, kind, control)
            n = len(design.outcome)
            k = design.regressors.shape[1]
            if n / k < MIN_OBSERVATIONS_PER_PARAMETER:
                valid = False
                break
            fitted = sm.OLS(design.outcome, design.regressors).fit()
            outcome_bics[name] = float(fitted.bic)
        if valid:
            rows.append(
                {
                    "model_kind": kind,
                    "control": control,
                    "p": p,
                    "q": q,
                    "summed_bic": float(sum(outcome_bics.values())),
                    "summed_aic": float(
                        sum(
                            sm.OLS(
                                build_model_design(frame, p, q, kind, control).outcome,
                                build_model_design(frame, p, q, kind, control).regressors,
                            )
                            .fit()
                            .aic
                            for frame in analysis_frames.values()
                        )
                    ),
                    "minimum_observations_per_parameter": float(
                        min(
                            len(build_model_design(frame, p, q, kind, control).outcome)
                            / build_model_design(frame, p, q, kind, control).regressors.shape[1]
                            for frame in analysis_frames.values()
                        )
                    ),
                    **{f"bic_{name}": value for name, value in outcome_bics.items()},
                }
            )
    if not rows:
        raise ValueError("No candidate lag structure passed the parameter-to-observation limit.")
    table = pd.DataFrame(rows).sort_values(["summed_bic", "p", "q"]).reset_index(drop=True)
    best = table.iloc[0]
    return int(best["p"]), int(best["q"]), table
