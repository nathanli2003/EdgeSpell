import pandas as pd
import numpy as np
import os
import glob

# ================= CONFIGURATION =================
TARGET_ROWS = 100
DEFAULT_INPUT_DIR = "runs"
DEFAULT_OUTPUT_DIR = "runs_normalized"
# =================================================

def normalize_run(data, target_length):
    """
    Takes a DataFrame or array of shape (N, 3) and returns (target_length, 3).
    - If N > target_length: Truncates data.
    - If N < target_length: Interpolates data.
    """
    data = data.dropna().to_numpy()
    current_length = len(data)

    if current_length == 0:
        return np.zeros((target_length, 3)) 

    if current_length > target_length:
        return data[:target_length]
    
    elif current_length < target_length:
        original_indices = np.arange(current_length)
        new_indices = np.linspace(0, current_length - 1, target_length)
        
        new_data = np.zeros((target_length, 3))
        for col in range(3):
            new_data[:, col] = np.interp(new_indices, original_indices, data[:, col])
            
        return new_data
    
    else:
        return data

def process_and_normalize_runs(input_dir, output_dir, target_rows):
    # 1. Check Input Directory
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return

    # 2. Check/Create Output Directory
    if not os.path.exists(output_dir):
        print(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir)

    # 3. Find all CSVs
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    if not csv_files:
        print(f"No CSV files found in '{input_dir}'.")
        return

    print(f"Found {len(csv_files)} files in '{input_dir}'...")

    # 4. Process Each File
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        base_name, extension = os.path.splitext(filename)
        print(f"[PROCESS] {filename}")

        try:
            df = pd.read_csv(file_path)
            
            num_runs = len(df.columns) // 3
            if num_runs == 0:
                print("   -> No data columns found.")
                continue

            # First pass: Get the number of valid rows for each run
            run_row_counts = []
            for i in range(num_runs):
                start_col = i * 3
                end_col = start_col + 3
                run_data = df.iloc[:, start_col:end_col]
                run_row_counts.append(len(run_data.dropna()))

            # Calculate statistics for row counts
            mean_rows = np.mean(run_row_counts)
            std_rows = np.std(run_row_counts)
            lower_bound = mean_rows - 1.5 * std_rows
            upper_bound = mean_rows + 1.5 * std_rows
            print(f"   -> Stats: Mean rows={mean_rows:.1f}, Std Dev={std_rows:.1f}. Valid range: [{lower_bound:.1f}, {upper_bound:.1f}]")

            # Second pass: Filter, normalize, and collect runs
            processed_runs = []
            for i in range(num_runs):
                if not (lower_bound <= run_row_counts[i] <= upper_bound):
                    cols_to_skip = df.columns[i*3 : i*3+3].tolist()
                    print(f"   -> Skipping run (cols: {cols_to_skip}): {run_row_counts[i]} rows is outside range.")
                    continue
                
                run_data = df.iloc[:, i*3 : i*3+3]
                normalized_data = normalize_run(run_data, target_rows)
                
                # Keep original column names
                cols = df.columns[i*3 : i*3+3]
                run_df = pd.DataFrame(normalized_data, columns=cols)
                processed_runs.append(run_df)

            if processed_runs:
                result_df = pd.concat(processed_runs, axis=1)

                # Construct new filename: [original_name]_normalized.csv
                output_filename = f"{base_name}_normalized{extension}"
                output_path = os.path.join(output_dir, output_filename)
                
                result_df.to_csv(output_path, index=False)
                print(f"   -> Saved to: {output_path}")
            else:
                print("   -> No valid runs to save after filtering.")

        except Exception as e:
            print(f"   -> Error processing file: {e}")

    print("\nProcessing complete.")

if __name__ == "__main__":
    process_and_normalize_runs(DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, TARGET_ROWS)