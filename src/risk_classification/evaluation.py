"""Classification metrics and validation-only decision thresholds."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


def classification_metrics(
    actual: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
    horizon: int,
    target_months: pd.Series | None = None,
) -> dict[str, Any]:
    """Calculate class-sensitive metrics while retaining undefined denominators."""
    y = np.asarray(actual, dtype=int)
    probability = np.asarray(probabilities, dtype=float)
    if y.ndim != 1 or probability.shape != y.shape or not len(y):
        raise ValueError("Actual labels and probabilities must be non-empty equal-length vectors.")
    if not np.isin(y, [0, 1]).all() or not np.isfinite(probability).all():
        raise ValueError("Labels must be binary and probabilities finite.")
    if ((probability < 0) | (probability > 1)).any():
        raise ValueError("Predicted probabilities must be between zero and one.")
    predicted = (probability >= threshold).astype(int)
    tp = int(((y == 1) & (predicted == 1)).sum())
    fp = int(((y == 0) & (predicted == 1)).sum())
    tn = int(((y == 0) & (predicted == 0)).sum())
    fn = int(((y == 1) & (predicted == 0)).sum())
    actual_positive = tp + fn
    actual_negative = tn + fp
    predicted_positive = tp + fp
    precision = tp / predicted_positive if predicted_positive else np.nan
    recall = tp / actual_positive if actual_positive else np.nan
    f1_denominator = 2 * tp + fp + fn
    f1 = 2 * tp / f1_denominator if f1_denominator else np.nan
    specificity = tn / actual_negative if actual_negative else np.nan
    fpr = fp / actual_negative if actual_negative else np.nan
    fnr = fn / actual_positive if actual_positive else np.nan
    positive_present = bool(actual_positive)
    both_classes_present = bool(actual_positive and actual_negative)
    if target_months is None:
        episode_sensitivity = np.nan
        actual_episodes = detected_episodes = 0
        missed_episodes = false_alarm_episodes = 0
    else:
        dates = pd.to_datetime(target_months).dt.to_period("M").reset_index(drop=True)
        order = np.argsort(dates.astype(str).to_numpy())
        sorted_y = y[order]
        sorted_predicted = predicted[order]
        sorted_dates = dates.iloc[order].reset_index(drop=True)
        def contiguous_positive_runs(values: np.ndarray) -> list[list[int]]:
            runs: list[list[int]] = []
            current: list[int] = []
            prior: pd.Period | None = None
            for index, (period, value) in enumerate(
                zip(sorted_dates, values, strict=True)
            ):
                if value:
                    if current and prior is not None and period.ordinal == prior.ordinal + 1:
                        current.append(index)
                    else:
                        if current:
                            runs.append(current)
                        current = [index]
                elif current:
                    runs.append(current)
                    current = []
                prior = period
            if current:
                runs.append(current)
            return runs

        actual_runs = contiguous_positive_runs(sorted_y)
        alert_runs = contiguous_positive_runs(sorted_predicted)
        actual_episodes = len(actual_runs)
        detected_episodes = sum(
            any(sorted_predicted[index] for index in run) for run in actual_runs
        )
        missed_episodes = actual_episodes - detected_episodes
        false_alarm_episodes = sum(
            not any(sorted_y[index] for index in run) for run in alert_runs
        )
        episode_sensitivity = (
            detected_episodes / actual_episodes if actual_episodes else np.nan
        )
    undefined: list[str] = []
    if not predicted_positive:
        undefined.append("precision: no predicted positive labels")
    if not actual_positive:
        undefined.append("recall/FNR/PR-AUC: no actual positive labels")
    if not actual_negative:
        undefined.append("specificity/FPR/ROC-AUC: no actual negative labels")
    if not f1_denominator:
        undefined.append("F1: no actual or predicted positive labels")
    if target_months is not None and not actual_episodes:
        undefined.append("episode_sensitivity: no observed elevated episodes")
    return {
        "n": int(len(y)),
        "actual_positive": actual_positive,
        "actual_negative": actual_negative,
        "predicted_positive": predicted_positive,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "accuracy": float((tp + tn) / len(y)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "pr_auc_average_precision": (
            float(average_precision_score(y, probability)) if positive_present else np.nan
        ),
        "roc_auc": (
            float(roc_auc_score(y, probability)) if both_classes_present else np.nan
        ),
        "brier_score": float(np.mean(np.square(probability - y))),
        "specificity": float(specificity),
        "false_positive_rate": float(fpr),
        "false_negative_rate": float(fnr),
        "false_alarms_per_year": float(fp / (len(y) / 12.0)),
        "actual_elevated_episodes": int(actual_episodes),
        "detected_elevated_episodes": int(detected_episodes),
        "missed_elevated_episodes": int(missed_episodes),
        "false_alarm_episodes": int(false_alarm_episodes),
        "episode_sensitivity": float(episode_sensitivity),
        "nominal_warning_lead_months": int(horizon),
        "undefined_metric_notes": "; ".join(undefined),
    }


def choose_f1_threshold(actual: np.ndarray, probabilities: np.ndarray) -> float:
    """Select an alert threshold using validation predictions only."""
    y = np.asarray(actual, dtype=int)
    probabilities = np.asarray(probabilities, dtype=float)
    if not len(y) or y.shape != probabilities.shape or not np.isin(y, [0, 1]).all():
        raise ValueError("Threshold selection requires aligned, non-empty binary validation data.")
    if not y.any():
        return 0.5
    candidates = np.unique(np.concatenate(([0.0, 0.5, 1.0], probabilities)))
    scores: list[tuple[float, int, float]] = []
    for threshold in candidates:
        predicted = probabilities >= threshold
        tp = int(((y == 1) & predicted).sum())
        fp = int(((y == 0) & predicted).sum())
        fn = int(((y == 1) & ~predicted).sum())
        denominator = 2 * tp + fp + fn
        f1 = 2 * tp / denominator if denominator else 0.0
        scores.append((f1, -fp, float(threshold)))
    return max(scores)[2]
