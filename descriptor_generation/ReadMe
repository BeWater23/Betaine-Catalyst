Descriptor generation folder guide
==================================

This folder contains the molecule lists, calculation logs, collected descriptor
tables, and helper scripts used to assemble model-ready descriptor matrices.
Most workflows start from the compact descriptor spreadsheets, not directly from
the raw log files.

Folder layout
-------------

- `comb_input_template.xlsx`: combined reaction template. The first two columns
  identify the catalyst and substrate, `ddG` is the target column, and the
  columns after `ddG` are descriptor columns to be filled.
- `fill_paramters.py`: fills descriptor columns in a combined template by
  matching catalyst and substrate IDs against descriptor summary tables.
- `catalysts/`: catalyst inputs and descriptors for the main data set.
  - `catalysts.xlsx`: SMILES and ID list.
  - `*.log`: calculation outputs kept for provenance.
  - `all_cats_descriptors.xlsx`: compact catalyst descriptor table used by
    `fill_paramters.py`.
- `substrates/`: substrate inputs and descriptors for the main data set.
  - `substrates.xlsx`: SMILES and ID list.
  - `*.log`: calculation outputs kept for provenance.
  - `all_substrates_descriptors.xlsx`: compact substrate descriptor table used
    by `fill_paramters.py`.
- `oos_catalysts/`: out-of-sample catalyst set. Use
  `oos_catalysts_descriptors.xlsx` when building external catalyst panels.
- `virtual_screening/`: virtual-screening substrate/analyte set. Use
  `vsa_descriptors.xlsx` when building virtual-screening panels.
- `sisso/`: feature-generation inputs, outputs, and scripts for reduced SISSO
  style interaction features.
  - `translation_file.xlsx`: lookup table mapping full descriptor names to the
    abbreviated `x1`-`x30` names used in the SISSO workbooks.


Recalculate descriptors from Gaussian output (.log) files
------------------------------------
Clone the Sigman-Lab script Get_Properties from Github: https://github.com/SigmanGroup/GetProperties
The repository contains all the instructions on how to extract steric and electronic properties from the .log files.


Building a combined descriptor table
------------------------------------

Run this command from inside `descriptor_generation/`:

```bash
python fill_paramters.py comb_input_template.xlsx catalysts/all_cats_descriptors.xlsx substrates/all_substrates_descriptors.xlsx
```

What the script expects:

- The input workbook has catalyst IDs in column 1, substrate IDs in column 2,
  and a `ddG` column.
- Every descriptor column to fill appears after `ddG`.
- Catalyst IDs must match the first column of the catalyst descriptor table.
- Substrate IDs must match the first column of the substrate descriptor table.
- Catalyst and substrate descriptor tables should not contain duplicate
  descriptor column names.

What the script does:

- Adds a `cat_substrate` ID by joining the first two columns.
- Fills catalyst descriptors from the catalyst descriptor table.
- Fills substrate descriptors from the substrate descriptor table.
- Prints warnings for missing catalysts, substrates, or descriptor columns.
- Saves changes back into the input workbook.

Because the script overwrites the input file, work on a copy if you need to keep
the original template unchanged. If the input already contains a `cat_substrate`
column, remove it before rerunning the script or use a fresh template copy.

For out-of-sample or virtual-screening panels, keep the same command pattern but
swap in the relevant descriptor table, for example:

```bash
python fill_paramters.py my_external_panel.xlsx oos_catalysts/oos_catalysts_descriptors.xlsx substrates/all_substrates_descriptors.xlsx
python fill_paramters.py my_virtual_screen.xlsx catalysts/all_cats_descriptors.xlsx virtual_screening/vsa_descriptors.xlsx
```

SISSO feature workflow
----------------------

Run these commands from inside `descriptor_generation/sisso/`:

```bash
python SISSO_reduced_feat_gen.py training_set_input.xlsx
python calculate_SISSO_features.py training_set_sisso_result.xlsx external_test_set_input.xlsx
```

`SISSO_reduced_feat_gen.py` expects a training workbook with:

- `cat_substrate`
- `ddG`
- numeric base feature columns named like `x1`, `x2`, `x4`, etc.

Use `translation_file.xlsx` to translate between the readable descriptor names
and the `x*` column names before or after running the SISSO scripts. The current
translation file contains abbreviations from `x1` through `x30`; the actual
training/test input files may contain only the selected subset used for the
model.

It expands the base features, filters generated interaction features, applies
Boruta feature selection, and writes an output named:

```text
<input_name>_SISSO_reduced_Boruta.xlsx
```

The saved `training_set_sisso_result.xlsx` file is the reduced training feature
set used by the test-set calculation command.

`calculate_SISSO_features.py` takes:

1. a reduced SISSO training/result workbook containing the selected augmented
   feature names, and
2. a new input workbook containing the same original `x*` base features.

It recomputes the selected augmented features for the new rows and writes:

```text
<new_input_name>_SISSO.xlsx
```

The saved `external_test_set_sisso_result.xlsx` file is the corresponding
external/test-set result.

