# AutoConf conformer-search scripts

Scripts for moving CREST/CENSO conformer ensembles through Chemshell/Turbomole optimizations, single-point calculations, energy sorting, and transition-state enantiomeric-excess estimates on the bwHPC/Justus2-style environment used for the project.

## Requirements

- Bash, Python 3, and NumPy.
- Cluster commands/modules used by the scripts, especially `bwHPC_chemshell`.
- Chemshell input templates (`*.chm`) for the optimization, single-point, TS, and numerical-frequency jobs.

The Chemshell templates are intentionally not hard-coded to a personal account path. Put them in `templates/` next to these scripts, or set:

```bash
export AUTOCONF_TEMPLATE_DIR=/path/to/chemshell/templates
```

Expected template names:

- `opt_constrained_m06-2x.chm`
- `opt_m06-2x_numfreq.chm`
- `spe_m06-2x_cosmo.chm`
- `ts_opt_m06-2x.chm`
- `spe_ts_m06-2x.chm`
- `numfreq_ts_m06-2x.chm`

## Workflow

### 1. Split and optimize a conformer ensemble

For minima:

```bash
./auto_opt.sh ensemble.xyz
```

For constrained optimizations used before TS searches:

```bash
./auto_opt.sh ensemble.xyz --constrain=3,5
```

The script splits the input XYZ ensemble into `censo_1`, `censo_2`, ... folders, copies the relevant Chemshell template, and submits the optimization jobs.

### 2. Process minima

After minima optimizations have converged:

```bash
./auto_spe_min.sh > auto_spe_min.out
./auto_energies.sh > auto_energies.out
```

`auto_spe_min.sh` starts SPE jobs for converged minima. `auto_energies.sh` extracts SPE and thermochemical contributions, writes `conformer_energies.txt`, and sorts relative free energies with `energy_sorting.py`.

### 3. Process TS conformers

After constrained optimizations have converged:

```bash
./auto_ts_opt.sh > auto_ts_opt.out
./auto_spe_ts.sh > auto_spe_ts.out
./auto_energies.sh --ts > auto_energies.out
```

`auto_ts_opt.sh` starts dimer TS optimizations from the constrained geometries and imaginary-mode structure. `auto_spe_ts.sh` starts SPE jobs and, when needed, numerical-frequency jobs. `auto_energies.sh --ts` extracts final TS energies, creates `ts_conformers.xyz`, and copies key outputs into `results/`.

### 4. Predict ee from major/minor TS folders

From a directory containing `ts_major/auto_energies.out` and `ts_minor/auto_energies.out`:

```bash
./predict_ee.sh
```

This writes `ee_prediction.txt` using `ee_prediction.py`.

### 5. Align combined TS conformers

To center all structures in `ts_conformers.xyz` at their geometric center:

```bash
python3 align_conformers.py
```

The aligned ensemble is written to `aligned_ts_conformers.xyz`.
