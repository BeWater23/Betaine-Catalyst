import pandas as pd
import sys

def load_and_prepare(file):
    # Load file and use first column as index
    df = pd.read_excel(file)
    df = df.set_index(df.columns[0])
    return df

def fill_parameters(input_file, catalyst_file, substrate_file):
    # Load input
    df_input = pd.read_excel(input_file)

    # --- Create combined ID column (cat_substrate) ---
    combined_id = df_input.iloc[:, 0].astype(str) + "_" + df_input.iloc[:, 1].astype(str)

    # Insert before 'ddG'
    try:
        ddg_index = df_input.columns.get_loc("ddG")
    except KeyError:
        raise ValueError("❌ ERROR: Could not find a 'ddG' column in input file.")
    df_input.insert(ddg_index, "cat_substrate", combined_id)

    # Identify parameter columns (everything after 'ddG')
    try:
        ddg_index = df_input.columns.get_loc("ddG")
    except KeyError:
        raise ValueError("❌ ERROR: Could not find a 'ddG' column in input file.")
    param_cols = df_input.columns[ddg_index+1:]

    # Load catalyst and substrate tables
    df_catalyst = load_and_prepare(catalyst_file)
    df_substrate = load_and_prepare(substrate_file)

    # Safety check for overlapping parameter names
    overlap = set(df_catalyst.columns) & set(df_substrate.columns)
    if overlap:
        raise ValueError(f"❌ ERROR: The following parameter names exist in BOTH catalyst and substrate files: {', '.join(overlap)}")
        
    # Check for missing catalyst/substrate IDs 
    missing_cats = set(df_input.iloc[:, 0]) - set(df_catalyst.index)
    if missing_cats:
        print(f"⚠️ WARNING: The following catalysts from input were not found in {catalyst_file}: {', '.join(map(str, missing_cats))}")

    missing_subs = set(df_input.iloc[:, 1]) - set(df_substrate.index)
    if missing_subs:
        print(f"⚠️ WARNING: The following substrates from input were not found in {substrate_file}: {', '.join(map(str, missing_subs))}")
        
    # Fill catalyst parameters
    for col in [c for c in param_cols if c in df_catalyst.columns]:
        df_input[col] = df_input.iloc[:, 0].map(df_catalyst[col])  # first column = cat

    # Fill substrate parameters
    for col in [c for c in param_cols if c in df_substrate.columns]:
        df_input[col] = df_input.iloc[:, 1].map(df_substrate[col])  # second column = substrate

    # Warn if parameters missing in both files
    missing_params = [c for c in param_cols if c not in df_catalyst.columns and c not in df_substrate.columns]
    if missing_params:
        print(f"⚠️ WARNING: The following parameters were not found in either catalyst or substrate files: {', '.join(missing_params)}")

    # Overwrite input file
    df_input.to_excel(input_file, index=False)
    print(f"✅ Parameters filled and saved back into {input_file}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python fill_parameters.py <input.xlsx> <catalyst.xlsx> <substrate.xlsx>")
        sys.exit(1)

    input_file, catalyst_file, substrate_file = sys.argv[1:4]
    fill_parameters(input_file, catalyst_file, substrate_file)
