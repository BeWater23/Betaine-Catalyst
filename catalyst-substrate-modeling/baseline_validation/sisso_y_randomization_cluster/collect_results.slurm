#!/usr/bin/env bash
#SBATCH --job-name=sisso-collect
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [[ -n "${PYTHON_EXECUTABLE:-}" ]]; then
    PYTHON_BIN="${PYTHON_EXECUTABLE}"
else
    if [[ -n "${CONDA_SETUP:-}" ]]; then
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

export MPLBACKEND=Agg
export MPLCONFIGDIR="${SLURM_TMPDIR:-/tmp}/matplotlib-${SLURM_JOB_ID}"
mkdir -p "${MPLCONFIGDIR}"

"${PYTHON_BIN}" -u collect_results.py \
    --n-shuffles "${N_SHUFFLES:?N_SHUFFLES was not exported}" \
    --output-root "${OUTPUT_ROOT:-${SCRIPT_DIR}/results}"
