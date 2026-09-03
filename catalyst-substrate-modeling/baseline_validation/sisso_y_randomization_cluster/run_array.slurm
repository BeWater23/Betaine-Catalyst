#!/usr/bin/env bash
#SBATCH --job-name=sisso-yperm
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err

set -euo pipefail

# Slurm runs a spool copy of this file, so BASH_SOURCE points to Slurm's spool
# directory. The submit helper exports the real repository directory; direct
# sbatch submissions fall back to the directory from which sbatch was called.
WORKFLOW_DIR="${SISSO_WORKFLOW_DIR:-${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is unavailable}}"
cd "${WORKFLOW_DIR}"

if [[ -n "${PYTHON_EXECUTABLE:-}" ]]; then
    PYTHON_BIN="${PYTHON_EXECUTABLE}"
else
    if [[ -n "${CONDA_SETUP:-}" ]]; then
        # Example: /path/to/miniconda3/etc/profile.d/conda.sh
        source "${CONDA_SETUP}"
    elif command -v conda >/dev/null 2>&1; then
        eval "$(conda shell.bash hook)"
    else
        echo "Set PYTHON_EXECUTABLE or CONDA_SETUP before submission." >&2
        exit 2
    fi
    conda activate "${CONDA_ENV_NAME:-sisso-y-randomization}"
    PYTHON_BIN="python"
fi

# Prevent BLAS/OpenMP threads from multiplying the Boruta worker count.
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export LOKY_MAX_CPU_COUNT="${SLURM_CPUS_PER_TASK:-1}"

"${PYTHON_BIN}" -u run_array_task.py \
    --permutation-index "${SLURM_ARRAY_TASK_ID}" \
    --output-root "${OUTPUT_ROOT:-${WORKFLOW_DIR}/results}" \
    --n-jobs "${SLURM_CPUS_PER_TASK:-1}"
