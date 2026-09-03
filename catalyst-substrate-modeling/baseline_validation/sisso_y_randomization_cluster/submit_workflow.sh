#!/usr/bin/env bash
# Submit the response tasks and dependent collector to Slurm.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"
mkdir -p logs

N_SHUFFLES="${N_SHUFFLES:-200}"
MAX_CONCURRENT="${MAX_CONCURRENT:-20}"
CPUS_PER_TASK="${CPUS_PER_TASK:-4}"
MEMORY="${MEMORY:-8G}"
TIME_LIMIT="${TIME_LIMIT:-02:00:00}"
PARTITION="${PARTITION:-}"
ACCOUNT="${ACCOUNT:-}"
QOS="${QOS:-}"

if ! [[ "${N_SHUFFLES}" =~ ^[1-9][0-9]*$ ]]; then
    echo "N_SHUFFLES must be a positive integer." >&2
    exit 2
fi
if ! [[ "${MAX_CONCURRENT}" =~ ^[1-9][0-9]*$ ]]; then
    echo "MAX_CONCURRENT must be a positive integer." >&2
    exit 2
fi
if ! [[ "${CPUS_PER_TASK}" =~ ^[1-9][0-9]*$ ]]; then
    echo "CPUS_PER_TASK must be a positive integer." >&2
    exit 2
fi

SBATCH_OPTIONS=(
    --parsable
    --array="0-${N_SHUFFLES}%${MAX_CONCURRENT}"
    --cpus-per-task="${CPUS_PER_TASK}"
    --mem="${MEMORY}"
    --time="${TIME_LIMIT}"
    --export="ALL,N_SHUFFLES=${N_SHUFFLES}"
)
if [[ -n "${PARTITION}" ]]; then
    SBATCH_OPTIONS+=(--partition="${PARTITION}")
fi
if [[ -n "${ACCOUNT}" ]]; then
    SBATCH_OPTIONS+=(--account="${ACCOUNT}")
fi
if [[ -n "${QOS}" ]]; then
    SBATCH_OPTIONS+=(--qos="${QOS}")
fi

ARRAY_SUBMISSION="$(sbatch "${SBATCH_OPTIONS[@]}" run_array.slurm)"
ARRAY_JOB_ID="${ARRAY_SUBMISSION%%;*}"

COLLECT_OPTIONS=(
    --parsable
    --dependency="afterok:${ARRAY_JOB_ID}"
    --export="ALL,N_SHUFFLES=${N_SHUFFLES}"
)
if [[ -n "${PARTITION}" ]]; then
    COLLECT_OPTIONS+=(--partition="${PARTITION}")
fi
if [[ -n "${ACCOUNT}" ]]; then
    COLLECT_OPTIONS+=(--account="${ACCOUNT}")
fi
if [[ -n "${QOS}" ]]; then
    COLLECT_OPTIONS+=(--qos="${QOS}")
fi

COLLECT_SUBMISSION="$(sbatch "${COLLECT_OPTIONS[@]}" collect_results.slurm)"
COLLECT_JOB_ID="${COLLECT_SUBMISSION%%;*}"

printf 'Array job:     %s\n' "${ARRAY_JOB_ID}"
printf 'Collector job: %s (afterok:%s)\n' "${COLLECT_JOB_ID}" "${ARRAY_JOB_ID}"
printf 'Configuration: %s permutations, at most %s simultaneous tasks\n' \
    "${N_SHUFFLES}" "${MAX_CONCURRENT}"
printf 'Per task:      %s CPUs, %s memory, %s wall time\n' \
    "${CPUS_PER_TASK}" "${MEMORY}" "${TIME_LIMIT}"
