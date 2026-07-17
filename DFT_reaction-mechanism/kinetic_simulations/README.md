# Kinetic Simulations

This folder contains the experimental kinetic-analysis notebook and the
concentration-time workbook used to fit rate laws for the reaction profile.

## Main Notebook

Use `kinetic_investigation.ipynb`.

The notebook is organized as a sequential analysis workflow. Run cells from top
to bottom because the fit sections reuse variables created during data loading,
especially `kinetics`, `c0_imino`, `c0_nmm`, `c_cat`, `k_fit_nmm`, and
`k2_fit_nmm`.

## How To Run

The notebook uses paths relative to this directory. Start Jupyter from
`DFT_reaction-mechanism/kinetic_simulations` or confirm the kernel working
directory is this folder before running cells.

```bash
cd DFT_reaction-mechanism/kinetic_simulations
jupyter lab kinetic_investigation.ipynb
```

## Input Data

The default input workbook is:

- `conc-time-profile.xlsx`

The notebook reads the first worksheet and extracts elapsed time plus the three
concentration series:

- `c(nmm)`
- `c(imino)`
- `c(product)`

The workbook currently also contains intermediate integration and conversion
columns, but the fit workflow uses the concentration columns above. Time values
are converted to elapsed minutes, then also stored as elapsed hours.

To analyze a different workbook, edit this line in the data-loading cell:

```python
excel_path = Path("conc-time-profile.xlsx")
```

The same data-loading cell also controls the analyzed time-point range:

```python
analysis_start = 0
analysis_stop = None
```

Use `analysis_start` and `analysis_stop` to fit only a subset of the time
points without editing the workbook.

## Workflow Sections

The notebook includes:

- imports, plotting style, and local cache setup
- workbook loading and column normalization
- concentration-time plot for NMM, iminoester, and product
- logarithmic concentration plot for checking first-order behavior
- first-order NMM/product fit with a fitted product-yield cap
- Eyring free-energy estimate from the first-order fit
- second-order NMM/product fit with a fitted product-yield cap
- Eyring free-energy estimate from the second-order fit
- comparison to the DFT barrier stored as `dG_dft`

## Fit Configuration

The current DFT comparison value is:

```python
dG_dft = 64.3  # kJ/mol
```

The first-order and second-order sections define the catalyst concentration and
an uncertainty range:

```python
c_cat = 0.0005 / 2.4
c_cat_max = 0.00025 / 2.4
c_cat_min = 0.00075 / 2.4
```

Check these values before reusing the notebook for a different kinetic run.

## Outputs

The fit cells save PNG and PDF plots in this directory:

- `kinetic_fit_1st_order_<input-stem>.png`
- `kinetic_fit_1st_order_<input-stem>.pdf`
- `kinetic_fit_2nd_order_<input-stem>.png`
- `kinetic_fit_2nd_order_<input-stem>.pdf`

`<input-stem>` comes from `excel_path.stem`. With the current default input,
rerunning the notebook writes files named with `conc-time-profile`. Existing
checked-in plot files are named with `results`, which reflects the workbook
stem used when those plots were generated.

Rerunning cells can overwrite plot files with the same names.

## Reproducibility

For exact reproduction:

- run cells in order from a kernel whose working directory is this folder
- keep the same input workbook and column names
- keep the same `analysis_start`, `analysis_stop`, `c_cat`, catalyst
  uncertainty range, and `dG_dft` settings
- keep the same Python environment and package versions
- archive old plot outputs before rerunning if you need to preserve them
