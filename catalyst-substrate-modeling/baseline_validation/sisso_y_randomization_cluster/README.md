# Slurm-array SISSO Y-randomization

This directory is the cluster-oriented companion to
`../sisso_y_randomization`. The local workflow is unchanged. The scientific
implementation is imported from that directory, while this wrapper changes
only orchestration and output handling.

## Parallelization model

Slurm array index 0 evaluates the observed response. Array index `N` evaluates
permutation `N`. Each task:

1. deterministically reconstructs the same permutation produced by the local
   sequential NumPy random-number stream;
2. runs all five outer folds with fold-level checkpoints;
3. assigns Boruta's random forest exactly `SLURM_CPUS_PER_TASK` workers;
4. writes only to `results/tasks/<response_id>`.

The array tasks therefore cannot overwrite each other's checkpoints or summary
tables. The five outer folds and 20 inner LASSO splits remain sequential within
one task; parallelism is across response permutations, with secondary
parallelism across Boruta trees.

## 1. Copy and create the environment

Copy the repository to a shared filesystem visible from the compute nodes, then
run on a login node:

```bash
cd catalyst-substrate-modeling/baseline_validation/sisso_y_randomization_cluster
conda env create -f environment.yml
```

The environment pins the main package versions used by the local `modeling`
environment and installs Boruta from its exact upstream commit.

If the cluster provides Conda through a module, load that module before creating
the environment. If its activation script is not automatically available to
batch jobs, export its path before submission, for example:

```bash
export CONDA_SETUP=/path/to/miniconda3/etc/profile.d/conda.sh
```

Alternatively, bypass Conda activation by exporting an absolute interpreter:

```bash
export PYTHON_EXECUTABLE=/path/to/environment/bin/python
```

## 2. Test one task

Validate imports, paths, the input hash, and permutation construction without
fitting:

```bash
python run_array_task.py --permutation-index 1 --dry-run
```

For a real single-task check:

```bash
python run_array_task.py --permutation-index 1 --n-jobs 4
```

Re-running the same command resumes completed outer folds.

## 3. Submit the array

The defaults are 200 permutations, at most 20 simultaneous array tasks, four
CPUs and 8 GB per task, and a two-hour limit per task:

```bash
conda activate sisso-y-randomization
./submit_workflow.sh
```

Override the number of permutations, concurrency, CPUs, memory, and wall time
without editing a file:

```bash
N_SHUFFLES=1000 \
MAX_CONCURRENT=25 \
CPUS_PER_TASK=8 \
MEMORY=16G \
TIME_LIMIT=04:00:00 \
./submit_workflow.sh
```

Optional Slurm routing settings are also supported:

```bash
PARTITION=compute ACCOUNT=my_project QOS=normal ./submit_workflow.sh
```

The available variables and defaults are:

| Variable | Default | Meaning |
|---|---:|---|
| `N_SHUFFLES` | `200` | Number of randomized responses; one additional observed-response task is submitted. |
| `MAX_CONCURRENT` | `20` | Maximum number of array tasks running simultaneously. |
| `CPUS_PER_TASK` | `4` | CPU cores assigned to each response calculation and used by Boruta. |
| `MEMORY` | `8G` | Memory assigned to each response calculation. |
| `TIME_LIMIT` | `02:00:00` | Wall-time limit for each array task. |
| `PARTITION` | unset | Optional Slurm partition. |
| `ACCOUNT` | unset | Optional Slurm project/account. |
| `QOS` | unset | Optional Slurm QoS. |

`submit_workflow.sh` submits indices `0..N_SHUFFLES` and then submits a small
collector job with an `afterok` dependency on the complete array. Values passed
through `submit_workflow.sh` override the corresponding default `#SBATCH`
resource lines. A concurrency limit is important: the default maximum requests
up to 80 CPUs at once (`20 tasks x 4 CPUs`) and up to 160 GB distributed across
those tasks (`20 tasks x 8 GB`). No GPU is required.

## 4. Results and monitoring

Per-task standard output and errors are written to `logs/`. Scientific
checkpoints are written as:

```text
results/tasks/permutation_0001/
├── COMPLETE.json
├── analysis_configuration.json
├── task_metadata.json
└── runs/permutation_0001/
    ├── fold_01/
    │   ├── fold_record.json
    │   ├── selected_augmented_features.txt
    │   ├── sisso.log
    │   └── test_predictions.csv
    ├── ...
    ├── fold_metrics.csv
    ├── predictions.csv
    └── summary.json
```

After all tasks succeed, merged tables and plots appear in `results/combined/`.
The collector verifies that all requested task markers and result files exist,
that configurations agree, and that every response has complete folds and OOF
predictions before calculating the null distribution and empirical p-values.

Useful Slurm commands include:

```bash
squeue -u "$USER"
tail -f logs/sisso-yperm_<array-job-id>_<task-id>.out
```

If an array task times out, resubmitting the workflow is safe: completed
response tasks and completed outer folds are reused. The collector can also be
run manually:

```bash
python collect_results.py --n-shuffles 200
```

Do not point multiple copies of the original local runner at one shared result
directory. Its top-level combined CSV files are not designed for concurrent
writes; the array wrapper in this directory is.
