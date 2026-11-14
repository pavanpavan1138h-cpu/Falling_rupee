"""Research plots generated only from observed data and Stage 3 estimates."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _save(figure: plt.Figure, path: Path) -> None:
    """Write one figure and release its plotting resources."""
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)


def generate_stage3_figures(
    panel: pd.DataFrame,
    coefficients: pd.DataFrame,
    response_tables: dict[str, pd.DataFrame],
    residuals: pd.DataFrame,
    stability: pd.DataFrame,
    robustness: pd.DataFrame,
    output_dir: Path,
) -> list[Path]:
    """Create the Stage 3 descriptive, coefficient, response, and diagnostic figures."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    fig, axis = plt.subplots(figsize=(11, 4))
    axis.plot(panel["date"], panel["fx_log_change_pct"], color="#2a5783", linewidth=1.1)
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(title="USD/INR monthly log change", ylabel="Log change (%)", xlabel="Month")
    axis.xaxis.set_major_locator(mdates.YearLocator(2))
    outputs.append(output_dir / "stage3_usd_inr_monthly_changes.png")
    _save(fig, outputs[-1])

    fig, axis = plt.subplots(figsize=(11, 4))
    axis.bar(panel["date"], panel["depreciation"], width=22, color="#bd4c39", label="Depreciation")
    axis.bar(panel["date"], panel["appreciation"], width=22, color="#356b91", label="Appreciation")
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(
        title="Signed depreciation and appreciation changes",
        ylabel="Log change (%)",
        xlabel="Month",
    )
    axis.legend()
    axis.xaxis.set_major_locator(mdates.YearLocator(2))
    outputs.append(output_dir / "stage3_depreciation_appreciation.png")
    _save(fig, outputs[-1])

    fig, axis = plt.subplots(figsize=(11, 4))
    axis.plot(
        panel["date"],
        panel["fx_positive_partial_sum"],
        label="Positive partial sum",
        color="#bd4c39",
    )
    axis.plot(
        panel["date"],
        panel["fx_negative_partial_sum"],
        label="Negative partial sum (signed)",
        color="#356b91",
    )
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(title="USD/INR signed cumulative partial sums", ylabel="Cumulative log-change points")
    axis.legend()
    axis.xaxis.set_major_locator(mdates.YearLocator(2))
    outputs.append(output_dir / "stage3_fx_partial_sums.png")
    _save(fig, outputs[-1])

    fig, axis = plt.subplots(figsize=(11, 5))
    for column, label, color in (
        ("cpi_annual_log_inflation", "CPI General (index-derived)", "#274c77"),
        (
            "wpi_all_commodities_annual_log_inflation",
            "WPI All Commodities (index-derived)",
            "#c44536",
        ),
    ):
        axis.plot(panel["date"], panel[column], label=label, linewidth=1.3, color=color)
    axis.set(
        title="Index-derived annual log inflation, common sample",
        ylabel="Annual log change (%)",
        xlabel="Month",
    )
    axis.legend()
    axis.xaxis.set_major_locator(mdates.YearLocator(2))
    outputs.append(output_dir / "stage3_cpi_wpi_annual_inflation.png")
    _save(fig, outputs[-1])

    asym = coefficients.loc[
        coefficients["model"].eq("asymmetric_baseline")
        & coefficients["term"].str.match(r"^(depreciation|appreciation)_lag_"),
    ].copy()
    fig, axis = plt.subplots(figsize=(10, 5))
    if not asym.empty:
        asym["label"] = asym["outcome"].str.replace("_annual_log_inflation", "", regex=False)
        positions = np.arange(len(asym))
        axis.errorbar(
            positions,
            asym["coefficient"],
            yerr=[
                asym["coefficient"] - asym["ci_95_lower"],
                asym["ci_95_upper"] - asym["coefficient"],
            ],
            fmt="o",
            capsize=2,
            color="#2a5783",
        )
        axis.axhline(0, color="black", linewidth=0.8)
        axis.set_xticks(positions)
        axis.set_xticklabels(
            [
                f"{row.outcome.replace('_annual_log_inflation', '')}\n{row.term}"
                for row in asym.itertuples()
            ],
            rotation=45,
            ha="right",
        )
    axis.set(
        title="Asymmetric distributed-lag coefficient estimates", ylabel="Coefficient (HAC 95% CI)"
    )
    outputs.append(output_dir / "stage3_asymmetric_coefficients.png")
    _save(fig, outputs[-1])

    fig, axis = plt.subplots(figsize=(9, 5))
    colors = plt.get_cmap("tab10")
    for index, (outcome, table) in enumerate(response_tables.items()):
        if table.empty:
            continue
        x = table["horizon_months"].to_numpy(dtype=float) + index * 0.05
        color = colors(index)
        axis.vlines(
            x,
            table["bootstrap_ci_95_lower"],
            table["bootstrap_ci_95_upper"],
            color=color,
            linewidth=1.2,
            alpha=0.8,
        )
        axis.scatter(
            x,
            table["asymmetry_contrast"],
            color=color,
            s=24,
            label=outcome.replace("_annual_log_inflation", ""),
        )
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set(
        title="Cumulative signed response asymmetry",
        xlabel="Months after a one-unit shock (including impact)",
        ylabel="Depreciation + equal-sized appreciation response",
    )
    axis.legend()
    outputs.append(output_dir / "stage3_cumulative_asymmetry_responses.png")
    _save(fig, outputs[-1])

    if not residuals.empty:
        names = residuals["model"].drop_duplicates().tolist()
        selected = residuals.loc[residuals["model"].isin(names[:2])]
        fig, axes = plt.subplots(
            len(selected["model"].unique()), 2, figsize=(10, 4 * len(selected["model"].unique()))
        )
        axes = np.atleast_2d(axes)
        for row, model in enumerate(selected["model"].unique()):
            subset = selected.loc[selected["model"].eq(model)]
            axes[row, 0].scatter(subset["fitted"], subset["residual"], s=14, alpha=0.75)
            axes[row, 0].axhline(0, color="black", linewidth=0.8)
            axes[row, 0].set(
                title=f"{model}: residuals vs fitted", xlabel="Fitted", ylabel="Residual"
            )
            axes[row, 1].plot(subset["date"], subset["residual"], color="#6a4c93")
            axes[row, 1].axhline(0, color="black", linewidth=0.8)
            axes[row, 1].set(title=f"{model}: residual sequence", xlabel="Month", ylabel="Residual")
        outputs.append(output_dir / "stage3_residual_diagnostics.png")
        _save(fig, outputs[-1])

    if not stability.empty:
        figure, axis = plt.subplots(figsize=(10, 5))
        for column in stability.columns:
            if column.endswith("_lag_0") and column not in {"date"}:
                axis.plot(stability["date"], stability[column], label=column)
        axis.set(
            title="Expanding-sample FX coefficient stability (descriptive)", ylabel="Coefficient"
        )
        axis.legend()
        outputs.append(output_dir / "stage3_coefficient_stability.png")
        _save(figure, outputs[-1])

    if not robustness.empty and {"specification", "bic_delta"}.issubset(robustness.columns):
        subset = robustness.dropna(subset=["bic_delta"])
        if not subset.empty:
            figure, axis = plt.subplots(figsize=(10, 5))
            axis.bar(subset["specification"], subset["bic_delta"], color="#588157")
            axis.axhline(0, color="black", linewidth=0.8)
            axis.tick_params(axis="x", labelrotation=35)
            axis.set(
                title="Robustness specification BIC differences",
                ylabel="BIC difference vs baseline",
            )
            outputs.append(output_dir / "stage3_robustness_bic.png")
            _save(figure, outputs[-1])
    return outputs
