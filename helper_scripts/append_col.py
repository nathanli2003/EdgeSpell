# Nano Edge requires all classes to have the same number of columns.
# This script appends CSV files with the same class prefixes and truncates them
# to ensure they all have the same number of columns.

# Reads from 'runs_normalized' directory and saves to 'runs_appended' directory.

import pandas as pd
import glob
import os

def append_columns_by_prefix(folder_path, output_folder):
    # The three prefixes we are looking for
    prefixes = ['leftright', 'rightleft', 'updown', 'downup']

    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)

    combined_data = {}
    original_column_counts = {}

    # --- STAGE 1: Read and combine files for each prefix in memory ---
    for prefix in prefixes:
        search_pattern = os.path.join(folder_path, f"{prefix}_*.csv")
        file_list = glob.glob(search_pattern)
        file_list.sort()

        if not file_list:
            print(f"No files found for prefix: {prefix}")
            continue
            
        print(f"[STAGE 1] Combining {len(file_list)} files for prefix '{prefix}'...")

        # 2. Read each file into a DataFrame
        dataframes = [pd.read_csv(file) for file in file_list]

        # 3. Concatenate along axis=1 (Columns)
        if dataframes:
            combined_df = pd.concat(dataframes, axis=1)
            combined_data[prefix] = combined_df
            original_column_counts[prefix] = combined_df.shape[1]
            print(f"-> Combined into a dataframe with {original_column_counts[prefix]} columns.")

    # --- STAGE 2: Find min columns, truncate, and save all files ---
    if not combined_data:
        print("\nNo data was combined. Exiting.")
        return {}

    print(f"\n[STAGE 2] Standardizing column counts across {len(combined_data)} combined datasets...")

    # 1. Find the global minimum number of columns from the in-memory dataframes
    min_cols_prefix, min_cols = min(original_column_counts.items(), key=lambda item: item[1])
    print(f"-> Class '{min_cols_prefix}' has the least columns ({min_cols}). Truncating all files to this size.")

    # 2. Truncate each dataframe and save the final result to a CSV file
    for prefix, df in combined_data.items():
        original_cols = df.shape[1]
        df_truncated = df.iloc[:, :min_cols]
        output_filename = os.path.join(output_folder, f"combined_{prefix}.csv")
        df_truncated.to_csv(output_filename, index=False)
        print(f"   - Saved {os.path.basename(output_filename)}: truncated from {original_cols} to {min_cols} columns.")
    
    return original_column_counts

if __name__ == "__main__":
    # Default configuration for standalone execution
    DEFAULT_INPUT_FOLDER = 'runs_normalized'
    DEFAULT_OUTPUT_FOLDER = 'runs_appended'

    original_counts = append_columns_by_prefix(DEFAULT_INPUT_FOLDER, DEFAULT_OUTPUT_FOLDER)
    if original_counts:
        print("\n--- Original Column Counts Before Truncation ---")
        for prefix, count in original_counts.items():
            print(f"- {prefix}: {count} columns")
        print("-------------------------------------------------")