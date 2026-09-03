#!/usr/bin/env python3
"""Validate and combine completed SISSO Y-randomization array tasks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import mean_absolute_error, r2_score  # noqa: E402


SCRIPT_DIR = Path(__file__).resolve().parent
LOCAL_WORKFLOW_DIR = SCRIPT_DIR.parent / "sisso_y_randomization"
if str(LOCAL_WORKFLOW_DIR) not in sys.path:
    sys.path.insert(0, str(LOCAL_WORKFLOW_DIR))

from plot_sisso_y_randomization import (  # noqa: E402
    feature_selection_frequency,
    plot_best_randomized_parity,
    plot_null_distributions,
    plot_top_feature_frequencies,
    save_figure,
)
from run_sisso_y_randomization import (  # noqa: E402
    ResponseEvaluation,
    _combine_results,
    _save_combined,
)


DEFAULT_OUTPUT_ROOT = SCRIPT_DIR / "results"


def response_id_for_index(index: int) -> str:
    return "observed" if index == 0 else f"permutation_{index:04d}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--n-shuffles", type=int, required=True)
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Combine available tasks instead of failing when an index is missing.",
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Only write combined CSV/JSON outputs.",
    )
    return parser


def load_task(task_dir: Path, expected_response_id: str) -> ResponseEvaluation:
    complete_path = task_dir / "COMPLETE.json"
    run_dir = task_dir / "runs" / expected_response_id
    summary_path = run_dir / "summary.json"
    folds_path = run_dir / "fold_metrics.csv"
    predictions_path = run_dir / "predictions.csv"
    required = [complete_path, summary_path, folds_path, predictions_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing completed-task files: " + ", ".join(missing))

    completion = json.loads(complete_path.read_text())
    summary = json.loads(summary_path.read_text())
    if completion.get("response_id") != expected_response_id:
        raise ValueError(f"Unexpected response ID in {complete_path}")
    if summary.get("response_id") != expected_response_id:
        raise ValueError(f"Unexpected response ID in {summary_path}")

    folds = pd.read_csv(folds_path).sort_values("outer_fold").reset_index(drop=True)
    predictions = pd.read_csv(predictions_path).sort_values("row_index").reset_index(
        drop=True
    )
    expected_folds = int(summary["n_outer_folds"])
    expected_rows = int(summary["n_observations"])
    if len(folds) != expected_folds or folds["outer_fold"].nunique() != expected_folds:
        raise ValueError(f"Incomplete or duplicate folds for {expected_response_id}")
    expected_indices = np.arange(expected_rows)
    if not np.array_equal(predictions["row_index"].to_numpy(dtype=int), expected_indices):
        raise ValueError(f"Incomplete or duplicate predictions for {expected_response_id}")
    if not np.all(np.isfinite(predictions[["response", "oof_prediction"]])):
        raise ValueError(f"Non-finite prediction values for {expected_response_id}")

    return ResponseEvaluation(
        label=expected_response_id,
        summary=summary,
        fold_metrics=folds,
        predictions=predictions,
    )


def validate_manifests(task_dirs: list[Path]) -> dict:
    manifests = []
    for task_dir in task_dirs:
        path = task_dir / "analysis_configuration.json"
        if not path.exists():
            raise FileNotFoundError(path)
        manifests.append(json.loads(path.read_text()))
    reference = manifests[0]
    for task_dir, manifest in zip(task_dirs[1:], manifests[1:]):
        if manifest != reference:
            raise ValueError(
                "Array tasks used different analysis configurations; first mismatch: "
                f"{task_dir}"
            )
    return reference


def validate_task_metadata(task_dirs: list[Path]) -> dict:
    metadata_records = []
    for task_dir in task_dirs:
        path = task_dir / "task_metadata.json"
        if not path.exists():
            raise FileNotFoundError(path)
        metadata_records.append(json.loads(path.read_text()))

    reference = metadata_records[0]
    invariant_keys = [
        "shuffle_scheme",
        "random_state",
        "input_file",
        "input_sha256",
        "scientific_source_sha256",
        "software_versions",
    ]
    for task_dir, metadata in zip(task_dirs[1:], metadata_records[1:]):
        mismatches = [
            key for key in invariant_keys if metadata.get(key) != reference.get(key)
        ]
        if mismatches:
            raise ValueError(
                f"Task metadata differs for {task_dir}; mismatched: {mismatches}"
            )
    return reference


def validate_evaluations(evaluations: list[ResponseEvaluation]) -> None:
    """Check target preservation and independently recompute OOF metrics."""

    observed = next(
        evaluation
        for evaluation in evaluations
        if evaluation.summary["response_kind"] == "observed"
    )
    observed_predictions = observed.predictions.sort_values("row_index")
    expected_ids = observed_predictions["cat_substrate"].astype(str).to_numpy()
    expected_values = np.sort(observed_predictions["response"].to_numpy(dtype=float))

    for evaluation in evaluations:
        predictions = evaluation.predictions.sort_values("row_index")
        identifiers = predictions["cat_substrate"].astype(str).to_numpy()
        if not np.array_equal(identifiers, expected_ids):
            raise ValueError(
                f"Observation identifiers differ for {evaluation.label}"
            )
        response = predictions["response"].to_numpy(dtype=float)
        if not np.array_equal(np.sort(response), expected_values):
            raise ValueError(
                f"{evaluation.label} is not a value-preserving response permutation"
            )
        oof_prediction = predictions["oof_prediction"].to_numpy(dtype=float)
        recomputed_r2 = float(r2_score(response, oof_prediction))
        recomputed_mae = float(mean_absolute_error(response, oof_prediction))
        if not np.isclose(recomputed_r2, evaluation.summary["oof_r2"], atol=1e-12):
            raise ValueError(f"OOF R2 mismatch for {evaluation.label}")
        if not np.isclose(recomputed_mae, evaluation.summary["oof_mae"], atol=1e-12):
            raise ValueError(f"OOF MAE mismatch for {evaluation.label}")


def main() -> None:
    args = build_parser().parse_args()
    if args.n_shuffles < 1:
        raise SystemExit("--n-shuffles must be at least 1.")

    output_root = args.output_root.resolve()
    tasks_root = output_root / "tasks"
    expected_ids = [response_id_for_index(i) for i in range(args.n_shuffles + 1)]
    complete_ids = [
        response_id
        for response_id in expected_ids
        if (tasks_root / response_id / "COMPLETE.json").exists()
    ]
    missing_ids = [response_id for response_id in expected_ids if response_id not in complete_ids]
    if missing_ids and not args.allow_incomplete:
        preview = ", ".join(missing_ids[:20])
        suffix = " ..." if len(missing_ids) > 20 else ""
        raise SystemExit(
            f"Cannot collect: {len(missing_ids)} task(s) are incomplete: {preview}{suffix}"
        )
    if "observed" not in complete_ids:
        raise SystemExit("Cannot collect without the observed-response task.")
    if not any(response_id.startswith("permutation_") for response_id in complete_ids):
        raise SystemExit("Cannot calculate a null distribution without a permutation.")

    task_dirs = [tasks_root / response_id for response_id in complete_ids]
    common_manifest = validate_manifests(task_dirs)
    common_metadata = validate_task_metadata(task_dirs)
    evaluations = [
        load_task(task_dir, response_id)
        for task_dir, response_id in zip(task_dirs, complete_ids)
    ]
    validate_evaluations(evaluations)
    result = _combine_results(evaluations)

    combined_dir = output_root / "combined"
    combined_dir.mkdir(parents=True, exist_ok=True)
    _save_combined(result, combined_dir)
    (combined_dir / "analysis_configuration.json").write_text(
        json.dumps(common_manifest, indent=2) + "\n"
    )
    feature_frequencies = feature_selection_frequency(result.fold_metrics, "observed")
    feature_frequencies.to_csv(
        combined_dir / "observed_feature_selection_frequency.csv",
        index=False,
    )
    pd.DataFrame(
        {
            "response_id": complete_ids,
            "task_directory": [str(path) for path in task_dirs],
        }
    ).to_csv(combined_dir / "completed_tasks.csv", index=False)
    (combined_dir / "collection_report.json").write_text(
        json.dumps(
            {
                "requested_permutations": args.n_shuffles,
                "completed_permutations": len(complete_ids) - 1,
                "missing_response_ids": missing_ids,
                "allow_incomplete": args.allow_incomplete,
                "shuffle_scheme": common_metadata["shuffle_scheme"],
                "scientific_source_sha256": common_metadata[
                    "scientific_source_sha256"
                ],
                "software_versions": common_metadata["software_versions"],
            },
            indent=2,
        )
        + "\n"
    )

    if not args.skip_plots:
        null_figure, _ = plot_null_distributions(
            result.response_summary,
            result.empirical_significance,
        )
        save_figure(null_figure, combined_dir / "sisso_y_randomization_null_distributions")

        parity_figure, _ = plot_best_randomized_parity(
            result.response_summary,
            result.predictions,
        )
        save_figure(parity_figure, combined_dir / "best_randomized_model_parity")

        if feature_frequencies.empty:
            print(
                "[notice] no observed-response augmented features were selected; "
                "skipping the feature-frequency plot",
                flush=True,
            )
        else:
            feature_figure, _ = plot_top_feature_frequencies(result.fold_metrics)
            save_figure(
                feature_figure,
                combined_dir / "observed_feature_selection_frequency",
            )

    print(
        f"[complete] collected {len(complete_ids) - 1} permutation(s) into "
        f"{combined_dir}",
        flush=True,
    )
    print(result.empirical_significance.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
