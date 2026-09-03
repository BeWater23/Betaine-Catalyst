#!/usr/bin/env python3
"""Run one observed or permuted-response SISSO/LASSO calculation.

The response index is normally supplied by ``SLURM_ARRAY_TASK_ID``. Index 0
is the observed response and index N is permutation N. Every task writes to a
different directory, so Slurm array tasks never update the same result files.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
LOCAL_WORKFLOW_DIR = SCRIPT_DIR.parent / "sisso_y_randomization"
if str(LOCAL_WORKFLOW_DIR) not in sys.path:
    sys.path.insert(0, str(LOCAL_WORKFLOW_DIR))

from nested_lasso import LassoConfig  # noqa: E402
from run_sisso_y_randomization import (  # noqa: E402
    ExperimentConfig,
    _prepare_output,
    evaluate_response,
    load_input_table,
)
from sisso_fold_features import SISSOConfig  # noqa: E402


DEFAULT_INPUT = SCRIPT_DIR.parent / "training_set_base.csv"
DEFAULT_LEGACY_SISSO_DIR = SCRIPT_DIR.parents[2] / "descriptor_generation" / "sisso"
DEFAULT_OUTPUT_ROOT = SCRIPT_DIR / "results"
SHUFFLE_SCHEME = "numpy-default-rng-sequential-v1"


def allocated_cpu_count() -> int:
    """Return the CPU allocation advertised by a common batch scheduler."""

    for variable in ("SLURM_CPUS_PER_TASK", "PBS_NP", "NSLOTS"):
        value = os.environ.get(variable)
        if value:
            try:
                return max(1, int(value))
            except ValueError:
                pass
    return 1


def response_for_index(
    observed: np.ndarray,
    permutation_index: int,
    random_state: int,
) -> np.ndarray:
    """Reproduce permutation N from the existing sequential local workflow.

    The local runner repeatedly calls ``rng.permutation(observed)``. Replaying
    those inexpensive draws makes every array task independent while retaining
    byte-for-byte agreement with local permutations generated using the same
    NumPy version and seed.
    """

    observed = np.asarray(observed, dtype=float)
    if permutation_index < 0:
        raise ValueError("permutation_index must be zero or positive.")
    if permutation_index == 0:
        return observed.copy()

    rng = np.random.default_rng(random_state)
    shuffled = observed.copy()
    for _ in range(permutation_index):
        shuffled = rng.permutation(observed)
    return np.asarray(shuffled, dtype=float)


def response_identity(permutation_index: int) -> tuple[str, str]:
    if permutation_index == 0:
        return "observed", "observed"
    return f"permutation_{permutation_index:04d}", "permuted"


def _atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scientific_source_hashes(legacy_sisso_dir: Path) -> dict[str, str]:
    sources = {
        "cluster_runner": Path(__file__).resolve(),
        "experiment_runner": LOCAL_WORKFLOW_DIR / "run_sisso_y_randomization.py",
        "nested_lasso": LOCAL_WORKFLOW_DIR / "nested_lasso.py",
        "sisso_fold_adapter": LOCAL_WORKFLOW_DIR / "sisso_fold_features.py",
        "legacy_sisso_generator": legacy_sisso_dir / "SISSO_reduced_feat_gen.py",
        "legacy_sisso_calculator": legacy_sisso_dir / "calculate_SISSO_features.py",
    }
    return {name: _sha256(path) for name, path in sources.items()}


def software_versions() -> dict[str, str]:
    packages = ["numpy", "pandas", "scikit-learn", "scipy", "Boruta"]
    versions = {"python": sys.version.split()[0]}
    for package in packages:
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--permutation-index",
        type=int,
        default=None,
        help="0 for observed y; N for permutation N. Defaults to SLURM_ARRAY_TASK_ID.",
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--legacy-sisso-dir",
        type=Path,
        default=DEFAULT_LEGACY_SISSO_DIR,
    )
    parser.add_argument("--outer-splits", type=int, default=5)
    parser.add_argument("--inner-splits", type=int, default=5)
    parser.add_argument("--inner-repeats", type=int, default=4)
    parser.add_argument("--n-bins", type=int, default=5)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--boruta-max-iter", type=int, default=100)
    parser.add_argument("--boruta-percentile", type=int, default=75)
    parser.add_argument("--collinearity-cutoff", type=float, default=0.8)
    parser.add_argument("--relative-filter-permutations", type=int, default=1_000)
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=None,
        help="Boruta/forest workers. Defaults to the scheduler CPU allocation.",
    )
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate paths and print task metadata without fitting models.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    permutation_index = args.permutation_index
    if permutation_index is None:
        array_value = os.environ.get("SLURM_ARRAY_TASK_ID")
        if array_value is None:
            raise SystemExit(
                "Supply --permutation-index or run inside a Slurm array task."
            )
        permutation_index = int(array_value)
    if permutation_index < 0:
        raise SystemExit("--permutation-index must be zero or positive.")

    n_jobs = allocated_cpu_count() if args.n_jobs is None else args.n_jobs
    if n_jobs < 1:
        raise SystemExit("--n-jobs must be at least 1.")

    input_file = args.input.resolve()
    legacy_sisso_dir = args.legacy_sisso_dir.resolve()
    output_root = args.output_root.resolve()
    response_id, response_kind = response_identity(permutation_index)
    task_output = output_root / "tasks" / response_id

    frame, base_features = load_input_table(input_file)
    observed = frame["ddG"].to_numpy(dtype=float)
    response = response_for_index(
        observed=observed,
        permutation_index=permutation_index,
        random_state=args.random_state,
    )

    lasso_config = LassoConfig(
        n_bins=args.n_bins,
        inner_splits=args.inner_splits,
        inner_repeats=args.inner_repeats,
        random_state=args.random_state,
    )
    sisso_config = SISSOConfig(
        legacy_sisso_dir=legacy_sisso_dir,
        collinearity_cutoff=args.collinearity_cutoff,
        relative_filter_permutations=args.relative_filter_permutations,
        boruta_percentile=args.boruta_percentile,
        boruta_max_iter=args.boruta_max_iter,
        random_state=args.random_state,
        n_jobs=n_jobs,
    )
    config = ExperimentConfig(
        input_file=input_file,
        output_dir=task_output,
        legacy_sisso_dir=legacy_sisso_dir,
        n_shuffles=0,
        outer_splits=args.outer_splits,
        n_bins=args.n_bins,
        random_state=args.random_state,
        resume=not args.no_resume,
        sisso=sisso_config,
        lasso=lasso_config,
    )

    metadata = {
        "response_id": response_id,
        "response_kind": response_kind,
        "permutation": permutation_index,
        "shuffle_scheme": SHUFFLE_SCHEME,
        "random_state": args.random_state,
        "n_jobs": n_jobs,
        "input_file": str(input_file),
        "input_sha256": _sha256(input_file),
        "response_sha256": hashlib.sha256(response.tobytes()).hexdigest(),
        "scientific_source_sha256": scientific_source_hashes(legacy_sisso_dir),
        "software_versions": software_versions(),
        "output_directory": str(task_output),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID", ""),
        "slurm_array_job_id": os.environ.get("SLURM_ARRAY_JOB_ID", ""),
        "slurm_array_task_id": os.environ.get("SLURM_ARRAY_TASK_ID", ""),
    }

    print(json.dumps(metadata, indent=2), flush=True)
    if args.dry_run:
        return

    task_output.mkdir(parents=True, exist_ok=True)
    _prepare_output(config)
    _atomic_json(task_output / "task_metadata.json", metadata)

    evaluation = evaluate_response(
        frame=frame,
        base_features=base_features,
        response=response,
        response_id=response_id,
        response_kind=response_kind,
        permutation=permutation_index,
        config=config,
    )
    pd.DataFrame([evaluation.summary]).to_csv(
        task_output / "response_summary.csv",
        index=False,
    )
    evaluation.fold_metrics.to_csv(task_output / "all_fold_metrics.csv", index=False)
    evaluation.predictions.to_csv(task_output / "all_predictions.csv", index=False)
    _atomic_json(
        task_output / "COMPLETE.json",
        {
            **metadata,
            "n_outer_folds": int(len(evaluation.fold_metrics)),
            "n_predictions": int(len(evaluation.predictions)),
            "oof_r2": float(evaluation.summary["oof_r2"]),
            "oof_mae": float(evaluation.summary["oof_mae"]),
        },
    )
    print(f"[complete] {response_id} -> {task_output}", flush=True)


if __name__ == "__main__":
    main()
