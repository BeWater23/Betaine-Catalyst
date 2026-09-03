#!/usr/bin/env bash
# Submit the response tasks and dependent collector to Slurm.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"
mkdir -p logs

N_SHUFFLES="${N_SHUFFLES:-200}"
MAX_CONCURRENT="${MAX_CONCURRENT:-20}"

if ! [[ "${N_SHUFFLES}" =~ ^[1-9][0-9]*$ ]]; then
    echo "N_SHUFFLES must be a positive integer." >&2
    exit 2
fi
if ! [[ "${MAX_CONCURRENT}" =~ ^[1-9][0-9]*$ ]]; then
    echo "MAX_CONCURRENT must be a positive integer." >&2
    exit 2
fi

ARRAY_SUBMISSION="$(sbatch --parsable \
    --array="0-${N_SHUFFLES}%${MAX_CONCURRENT}" \
    --export="ALL,N_SHUFFLES=${N_SHUFFLES}" \
    run_array.slurm)"
ARRAY_JOB_ID="${ARRAY_SUBMISSION%%;*}"

COLLECT_SUBMISSION="$(sbatch --parsable \
    --dependency="afterok:${ARRAY_JOB_ID}" \
    --export="ALL,N_SHUFFLES=${N_SHUFFLES}" \
    collect_results.slurm)"
COLLECT_JOB_ID="${COLLECT_SUBMISSION%%;*}"

printf 'Array job:     %s\n' "${ARRAY_JOB_ID}"
printf 'Collector job: %s (afterok:%s)\n' "${COLLECT_JOB_ID}" "${ARRAY_JOB_ID}"
