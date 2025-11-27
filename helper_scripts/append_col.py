import pandas as pd
import glob
import os
import numpy as np

def append_columns_by_prefix(folder_path, output_folder):
    # The three prefixes we are looking for
    prefixes = ['left_right', 'right_left', 'up_down']
    
    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)

    combined_files = []

    # --- STAGE 1: Combine files for each prefix without truncation ---
    for prefix in prefixes:
        # 1. Find all files matching the prefix pattern in the folder
        search_pattern = os.path.join(folder_path, f"{prefix}_*.csv")
        file_list = glob.glob(search_pattern)
        file_list.sort()
        
        if not file_list:
            print(f"No files found for prefix: {prefix}")
            continue
            
        print(f"[STAGE 1] Combining {len(file_list)} files for prefix '{prefix}'...")

        # 2. Read each file into a DataFrame
        dataframes = []
        for file in file_list:
            try:
                df = pd.read_csv(file)
                dataframes.append(df)
            except Exception as e:
                print(f"Error reading {file}: {e}")

        # 3. Concatenate along axis=1 (Columns)
        if dataframes:
            combined_df = pd.concat(dataframes, axis=1)
            
            # Save the result
            output_filename = os.path.join(output_folder, f"combined_{prefix}.csv")
            combined_df.to_csv(output_filename, index=False)
            combined_files.append(output_filename)
            print(f"-> Saved intermediate file with {combined_df.shape[1]} columns to: {output_filename}")

    # --- STAGE 2: Find the minimum column count and truncate all combined files ---
    if not combined_files:
        print("\nNo combined files were created. Exiting.")
        return

    print(f"\n[STAGE 2] Standardizing column counts across {len(combined_files)} combined files...")
    
    # 1. Find the global minimum number of columns
    min_cols = min(pd.read_csv(f).shape[1] for f in combined_files)
    print(f"-> Global minimum column count is {min_cols}. Truncating all combined files to this size.")

    # 2. Re-read, truncate, and overwrite each combined file
    for file_path in combined_files:
        df = pd.read_csv(file_path)
        if df.shape[1] > min_cols:
            df_truncated = df.iloc[:, :min_cols]
            df_truncated.to_csv(file_path, index=False)
            print(f"   - Truncated {os.path.basename(file_path)} from {df.shape[1]} to {min_cols} columns.")

if __name__ == "__main__":
    # Default configuration for standalone execution
    DEFAULT_INPUT_FOLDER = 'runs_normalized'
    DEFAULT_OUTPUT_FOLDER = 'runs_appended'

    append_columns_by_prefix(DEFAULT_INPUT_FOLDER, DEFAULT_OUTPUT_FOLDER)