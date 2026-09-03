"""Plotting helpers for fold-local SISSO Y-randomization results."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_null_distributions(
    response_summary: pd.DataFrame,
    empirical_significance: pd.DataFrame,
):
    """Plot OOF R2 and MAE null distributions with observed references."""

    observed = response_summary.loc[
        response_summary["response_kind"] == "observed"
    ].iloc[0]
    null = response_summary.loc[
        response_summary["response_kind"] == "permuted"
    ]
    if null.empty:
        raise ValueError("No completed permutations are available to plot.")
    p_values = empirical_significance.set_index("metric")["p_value"]
    specifications = [
        ("oof_r2", r"OOF $R^2$"),
        ("oof_mae", "OOF MAE"),
    ]

    figure, axes = plt.subplots(1, 2, figsize=(6, 2.8))
    for axis, (metric, label) in zip(axes, specifications):
        axis.hist(
            null[metric],
            bins=min(20, max(5, len(null))),
            color="lightgray",
            edgecolor="black",
            linewidth=0.6,
        )
        axis.axvline(
            observed[metric],
            color="#9E2A2B",
            linestyle="--",
            linewidth=1.2,
        )
        axis.set_xlabel(label)
        axis.set_ylabel("Count")
        axis.set_title(
            f"Observed = {observed[metric]:.3f}\n"
            f"p = {p_values.loc[metric]:.4f}"
        )
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
    figure.suptitle(f"Fold-local SISSO Y-randomization (n = {len(null)})")
    figure.tight_layout()
    return figure, axes


def plot_best_randomized_parity(
    response_summary: pd.DataFrame,
    predictions: pd.DataFrame,
):
    """Plot OOF predictions for the permutation with the highest OOF R2."""

    null = response_summary.loc[
        response_summary["response_kind"] == "permuted"
    ]
    if null.empty:
        raise ValueError("No completed permutations are available to plot.")
    best = null.loc[null["oof_r2"].idxmax()]
    best_predictions = predictions.loc[
        predictions["response_id"] == best["response_id"]
    ].sort_values("row_index")
    if best_predictions.empty:
        raise ValueError(f"No predictions found for {best['response_id']}")

    y_true = best_predictions["response"].to_numpy(dtype=float)
    y_pred = best_predictions["oof_prediction"].to_numpy(dtype=float)
    lower = min(y_true.min(), y_pred.min()) - 0.2
    upper = max(y_true.max(), y_pred.max()) + 0.2

    figure, axis = plt.subplots(figsize=(3.3, 2.8))
    axis.scatter(y_true, y_pred, color="#B8860B", alpha=0.65, s=30)
    axis.plot([lower, upper], [lower, upper], "k--", linewidth=1, alpha=0.3)
    axis.set_xlim(lower, upper)
    axis.set_ylim(lower, upper)
    axis.set_xlabel(r"Randomized measured $\Delta\Delta G^{\ddagger}$ (kcal/mol)")
    axis.set_ylabel(r"OOF-predicted $\Delta\Delta G^{\ddagger}$ (kcal/mol)")
    axis.set_title(f"Best randomized model #{int(best['permutation'])}")
    stats = (
        f"Mean in-fold $R^2$ = {best['mean_in_fold_r2']:.3f}\n"
        f"Mean in-fold MAE = {best['mean_in_fold_mae']:.3f}\n"
        f"OOF $R^2$ = {best['oof_r2']:.3f}\n"
        f"OOF MAE = {best['oof_mae']:.3f}\n"
        f"median alpha(1-SE) = {best['alpha_1se_median']:.5f}"
    )
    axis.text(
        0.03,
        0.97,
        stats,
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.75,
        },
    )
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    figure.tight_layout()
    return figure, axis


def feature_selection_frequency(
    fold_metrics: pd.DataFrame,
    response_kind: str = "observed",
) -> pd.DataFrame:
    """Calculate outer-fold selection frequencies for augmented features."""

    selected_rows = fold_metrics.loc[
        fold_metrics["response_kind"] == response_kind,
        "selected_augmented_features",
    ]
    counts: dict[str, int] = {}
    for value in selected_rows.fillna(""):
        for feature in filter(None, str(value).split(";")):
            counts[feature] = counts.get(feature, 0) + 1
    denominator = len(selected_rows)
    result = pd.DataFrame(
        [
            {
                "feature": feature,
                "selection_count": count,
                "selection_frequency": count / denominator,
            }
            for feature, count in counts.items()
        ]
    )
    if result.empty:
        return pd.DataFrame(
            columns=["feature", "selection_count", "selection_frequency"]
        )
    return result.sort_values(
        ["selection_frequency", "feature"],
        ascending=[False, True],
    ).reset_index(drop=True)


def plot_top_feature_frequencies(
    fold_metrics: pd.DataFrame,
    top_n: int = 20,
):
    """Plot the most frequently selected augmented features for observed y."""

    frequencies = feature_selection_frequency(fold_metrics, "observed").head(top_n)
    if frequencies.empty:
        raise ValueError("No augmented features were selected for observed y.")
    plot_data = frequencies.sort_values("selection_frequency")
    height = max(3.0, 0.28 * len(plot_data))
    figure, axis = plt.subplots(figsize=(6.5, height))
    axis.barh(
        plot_data["feature"],
        plot_data["selection_frequency"],
        color="#557A95",
    )
    axis.set_xlim(0, 1)
    axis.set_xlabel("Selection frequency across observed-response outer folds")
    axis.set_ylabel("")
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    figure.tight_layout()
    return figure, axis


def save_figure(figure, path: Path, dpi: int = 300) -> None:
    """Save one figure as both PNG and PDF."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    png_path = path.with_suffix(".png")
    pdf_path = path.with_suffix(".pdf")
    figure.savefig(png_path, dpi=dpi, bbox_inches="tight")
    figure.savefig(pdf_path, bbox_inches="tight")
