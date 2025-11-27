import os
import shutil

# Import the main functions from the other helper scripts
from normalize import process_and_normalize_runs, TARGET_ROWS
from append_col import append_columns_by_prefix
from remove_mag import remove_mag_columns

# ================= CONFIGURATION =================
DIR_RAW = "runs"
DIR_NORMALIZED = "runs_normalized"
DIR_APPENDED = "runs_appended"
DIR_NO_MAG = "run_no_mag"
# =================================================

def main():
    """
    Runs the full post-processing pipeline by executing the helper scripts in sequence.
    """
    print("="*50)
    print("STARTING POST-PROCESSING PIPELINE")
    print("="*50)

    # --- Step 1: Normalize raw data ---
    print("\n[STEP 1/3] Running Normalization...")
    process_and_normalize_runs(DIR_RAW, DIR_NORMALIZED, TARGET_ROWS)

    # --- Step 2: Append columns from normalized files ---
    print("\n[STEP 2/3] Running Column Appending...")
    append_columns_by_prefix(DIR_NORMALIZED, DIR_APPENDED)

    # --- Step 3: Remove magnetometer columns ---
    print("\n[STEP 3/3] Running Magnetometer Column Removal...")
    remove_mag_columns(DIR_APPENDED, DIR_NO_MAG)

    print("\n" + "="*50)
    print("POST-PROCESSING PIPELINE COMPLETE!")
    print(f"Final output located in: '{DIR_NO_MAG}'")
    print("="*50)

if __name__ == "__main__":
    main()