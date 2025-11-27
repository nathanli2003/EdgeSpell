import pandas as pd
import os

# Default configuration
DEFAULT_INPUT_DIR = 'runs_appended'
DEFAULT_OUTPUT_DIR = 'run_no_mag'

def remove_mag_columns(input_dir, output_dir):
    """
    Scans an input directory for CSV files, removes any columns containing
    'Mag' in their header, and saves the result to an output directory.
    """
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # List all files in the input directory
    try:
        csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    except FileNotFoundError:
        print(f"Error: The directory '{input_dir}' was not found.")
        return

    # Process each CSV file
    for file_name in csv_files:
        input_file_path = os.path.join(input_dir, file_name)
        output_file_path = os.path.join(output_dir, file_name)

        # Read the CSV file
        try:
            df = pd.read_csv(input_file_path)
            cols_to_drop = [col for col in df.columns if 'Mag' in col]
            df_modified = df.drop(columns=cols_to_drop)
            df_modified.to_csv(output_file_path, index=False)
            print(f"Processed {file_name}: dropped {len(cols_to_drop)} columns.")
        except Exception as e:
            print(f"Error processing {file_name}: {e}")

    print("Processing complete.")

if __name__ == "__main__":
    remove_mag_columns(DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR)
