# Catalyst-Only Modeling

This folder stores the catalyst-only modeling input table and one saved model
plot. The modeling code itself is not vendored here; it was run with the public
SigmanGroup `python-modeling` workflow:

<https://github.com/SigmanGroup/python-modeling>

## Contents

- `training_plus_val_set.xlsx`: catalyst-only feature table for modeling.
- `model_0_parity_publication.png`: saved parity plot from a completed model
  run.

## Input Workbook

`training_plus_val_set.xlsx` contains one sheet:

- `summary_all_cats`

Current workbook structure:

- 28 catalyst rows
- 374 columns
- first columns: `Catalyst`, `ddG`, then catalyst descriptors

Use `Catalyst` as the catalyst identifier column and `ddG` as the response
column unless intentionally changing the modeling target.

## Modeling Workflow

Use the upstream SigmanGroup repository for the actual modeling notebook and
environment files. The upstream README documents the conda environment and
notebook-based workflow.

Typical use:

1. Clone or download `SigmanGroup/python-modeling`.
2. Create the modeling environment from the upstream `modeling_env.yml`.
3. Copy `training_plus_val_set.xlsx` into the upstream `InputData/` folder.
4. Open `Mattlab_modeling_v6.0.0.ipynb`.
5. Configure the notebook to read:
   - workbook: `training_plus_val_set.xlsx`
   - sheet: `summary_all_cats`
   - identifier: `Catalyst`
   - response: `ddG`
6. Run the notebook cells in sequence.

If jumping around in the upstream notebook, run the train/validation/test split
setup before running modeling cells.

## Notes

- This folder is intended to preserve the feature set and selected exported
  results, not the full modeling code.
- Keep the source workbook unchanged when possible. Copy it into the upstream
  `InputData/` folder for modeling runs.
- If new plots or tables are generated, save them here with descriptive names
  so they can be traced back to the same input workbook.
