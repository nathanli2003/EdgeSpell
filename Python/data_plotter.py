import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as st

# ========================= CONFIGURATION =========================
# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'Data', 'dataset_train')
PLOT_DIR = os.path.join(BASE_DIR, '..', 'Data', 'plots')

# Signal Properties
FEATURES = ["Accel_X", "Accel_Y", "Accel_Z", "Gyro_X", "Gyro_Y", "Gyro_Z"]
NUM_FEATURES = len(FEATURES)
SAMPLE_NORM = 100  # Should match the value in post_processing.py
CONFIDENCE_LEVEL = 0.95
# =================================================================

def load_and_reshape_data(filepath, num_samples, num_features):
    """
    Loads a 'wide' format CSV and reshapes it into a 3D numpy array.

    Args:
        filepath (str): Path to the CSV file.
        num_samples (int): The number of time steps per run (e.g., 100).
        num_features (int): The number of features per sample (e.g., 6).

    Returns:
        np.ndarray: A 3D array of shape (num_runs, num_samples, num_features),
                    or None if the file is empty or invalid.
    """
    try:
        df = pd.read_csv(filepath)
        if df.empty:
            return None
        
        # Convert dataframe to a 2D numpy array
        wide_data = df.to_numpy()
        
        # Reshape the data: (num_runs, num_samples * num_features) -> (num_runs, num_samples, num_features)
        num_runs = wide_data.shape[0]
        reshaped_data = wide_data.reshape(num_runs, num_samples, num_features)
        
        return reshaped_data
    except (FileNotFoundError, pd.errors.EmptyDataError, ValueError) as e:
        print(f"Could not process file {os.path.basename(filepath)}: {e}")
        return None

def main():
    """
    Main function to generate and save the plots.
    """
    print("Starting data plotting process...")
    
    # Ensure plot directory exists
    os.makedirs(PLOT_DIR, exist_ok=True)
    
    # Find all training data files
    search_path = os.path.join(DATA_DIR, "*_training.csv")
    csv_files = glob.glob(search_path)
    
    if not csv_files:
        print(f"No training CSV files found in '{DATA_DIR}'.")
        print("Please run post_processing.py to generate the datasets.")
        return

    class_data = {}
    for f in csv_files:
        class_name = os.path.basename(f).replace("_training.csv", "")
        print(f"Loading data for class: '{class_name}'")
        data = load_and_reshape_data(f, SAMPLE_NORM, NUM_FEATURES)
        if data is not None:
            class_data[class_name] = data

    if not class_data:
        print("No valid data was loaded. Aborting plot generation.")
        return

    # Create a 3x2 subplot grid
    fig, axes = plt.subplots(3, 2, figsize=(15, 12), sharex=True)
    fig.suptitle('Average Signal for Each Class with 95% Confidence Interval', fontsize=16)
    
    # Flatten the axes array for easy iteration
    axes = axes.flatten()

    time_steps = np.arange(SAMPLE_NORM)

    # Plot data for each feature on its own subplot
    for i, feature_name in enumerate(FEATURES):
        ax = axes[i]
        for class_name, data in class_data.items():
            # data shape: (num_runs, num_samples, num_features)
            
            # Extract the data for the current feature
            feature_data = data[:, :, i] # Shape: (num_runs, num_samples)
            
            # Calculate the mean across all runs
            mean_signal = np.mean(feature_data, axis=0)
            
            # Calculate the confidence interval
            sem = st.sem(feature_data, axis=0)
            ci = sem * st.t.ppf((1 + CONFIDENCE_LEVEL) / 2., len(data)-1)
            
            # Plot the average signal
            line, = ax.plot(time_steps, mean_signal, label=class_name)
            
            # Plot the confidence interval as a filled area
            ax.fill_between(time_steps, mean_signal - ci, mean_signal + ci, color=line.get_color(), alpha=0.1)

        ax.set_title(feature_name)
        ax.set_ylabel("Sensor Value")
        ax.grid(True, linestyle='--', alpha=0.6)
        if i >= 4: # Only add x-label to bottom plots
            ax.set_xlabel("Time Steps")

    # Add a single legend for the entire figure
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper right', bbox_to_anchor=(0.95, 0.9))

    plt.tight_layout(rect=[0, 0, 1, 0.96]) # Adjust layout to make room for suptitle

    # Save the figure
    plot_filename = os.path.join(PLOT_DIR, 'class_signal_averages.png')
    plt.savefig(plot_filename)
    
    print(f"\nPlot saved successfully to '{plot_filename}'")

if __name__ == '__main__':
    main()
