
import os
import glob
import pandas as pd
import numpy as np
import scipy.stats as st
import matplotlib.pyplot as plt

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) # Should be the EdgeSpell root
EVALUATION_DIR = os.path.join(BASE_DIR, 'Data', 'evaluation')
PLOTS_DIR = os.path.join(BASE_DIR, 'Data', 'plots')

def parse_filename_info(filename):
    """
    Parses the filename to extract class, trainer, and model.
    Expected Format: [class]_[trainer]_[model]_inference_[timestamp].csv
    Example: downup_ne_rf_inference_20251211_204231.csv
    """
    basename = os.path.basename(filename)
    if basename.lower().endswith('.csv'):
        basename = basename[:-4]
    parts = basename.split('_')
    # We need at least class, trainer, model (3 parts)
    if len(parts) < 3:
        return None
    
    return {
        'class': parts[0],
        'trainer': parts[1],
        'model': parts[2]
    }

def format_class_name(class_name):
    """Formats class names for display."""
    label_map = {
        "rightleft": "Swipe Left",
        "leftright": "Swipe Right",
        "updown": "Swipe Down",
        "downup": "Swipe Up",
        "circle": "Circle",
        "lightning": "Lightning"
    }
    return label_map.get(class_name, class_name)

def load_data(eval_dir):
    """
    Loads all CSVs and aggregates them into a single DataFrame with metadata.
    """
    csv_files = glob.glob(os.path.join(eval_dir, '*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in {eval_dir}")
        return pd.DataFrame()

    data_frames = []
    for f in csv_files:
        info = parse_filename_info(f)
        if not info:
            print(f"Skipping file with unexpected format: {os.path.basename(f)}")
            continue
            
        try:
            df = pd.read_csv(f)
            if df.empty:
                continue

            # Add metadata columns
            df['ground_truth'] = format_class_name(info['class'])
            df['trainer'] = info['trainer']
            df['model'] = info['model']
            df['model_id'] = f"{info['trainer']}_{info['model']}"
            
            # Clean classification column (remove potential suffixes like '_training')
            if 'Classification' in df.columns:
                preds = df['Classification'].str.replace('_training', '', regex=False)
                df['predicted'] = preds.apply(format_class_name)
            
            data_frames.append(df)
        except Exception as e:
            print(f"Error reading {os.path.basename(f)}: {e}")

    if not data_frames:
        return pd.DataFrame()

    return pd.concat(data_frames, ignore_index=True)

def format_model_id(model_id):
    """Formats model_id for display on plots."""
    label_map = {
        'hm': 'In-House', 
        'ne': 'NanoEdge', 
        'mlp': 'MLP', 
        'rf': 'RF'
    }
    parts = model_id.split('_')
    if len(parts) == 2:
        trainer, model_type = parts
        return f"{label_map.get(trainer, trainer)} {label_map.get(model_type, model_type)}"
    return model_id # fallback

def plot_gesture_metrics(df, plots_dir):
    """
    Creates bar charts for each gesture comparing models (Accuracy & Time).
    """
    gestures = df['ground_truth'].unique()
    
    for gesture in gestures:
        gesture_df = df[df['ground_truth'] == gesture]
        models = sorted(gesture_df['model_id'].unique())
        
        acc_means, acc_cis = [], []
        time_means, time_cis = [], []
        
        for model in models:
            model_data = gesture_df[gesture_df['model_id'] == model]
            
            # --- Accuracy Stats ---
            # 1 if correct, 0 if incorrect
            is_correct = (model_data['predicted'] == model_data['ground_truth']).astype(int)
            acc = np.mean(is_correct)
            n = len(is_correct)
            # 95% CI for proportion: 1.96 * sqrt(p(1-p)/n)
            acc_ci = 1.96 * np.sqrt((acc * (1 - acc)) / n) if n > 0 else 0
            
            acc_means.append(acc)
            acc_cis.append(acc_ci)
            
            # --- Time Stats ---
            times = model_data['Inference Time (us)']
            t_mean = np.mean(times)
            t_sem = st.sem(times)
            # 95% CI for mean: t_score * sem
            t_ci = t_sem * st.t.ppf((1 + 0.95) / 2., len(times)-1) if len(times) > 1 else 0
            
            time_means.append(t_mean)
            time_cis.append(t_ci)

        # --- Plotting ---
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f'Metrics for Gesture: {gesture}', fontsize=16)
        
        x_pos = np.arange(len(models))
        model_labels = [format_model_id(m) for m in models]
        
        # Use a qualitative colormap for distinct colors per model
        colors = plt.get_cmap('tab10')(np.linspace(0, 1, len(models)))
        
        # Accuracy Subplot
        ax1.bar(x_pos, acc_means, yerr=acc_cis, capsize=5, color=colors, alpha=0.8)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(model_labels, rotation=45, ha='right')
        ax1.set_ylabel('Accuracy')
        ax1.set_ylim(0, 1.1)
        ax1.set_title('Classification Accuracy')
        ax1.grid(axis='y', linestyle='--', alpha=0.5)
        
        # Time Subplot
        ax2.bar(x_pos, time_means, yerr=time_cis, capsize=5, color=colors, alpha=0.8)
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(model_labels, rotation=45, ha='right')
        ax2.set_ylabel('Time (us)')
        ax2.set_title('Inference Time')
        ax2.grid(axis='y', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        filename = os.path.join(plots_dir, f'metrics_{gesture}.png')
        plt.savefig(filename)
        plt.close()
        print(f"Saved metrics plot for gesture '{gesture}' to {filename}")

def plot_confusion_matrices(df, plots_dir):
    """
    Creates a confusion matrix for each model configuration.
    """
    models = sorted(df['model_id'].unique())
    classes = sorted(df['ground_truth'].unique())
    
    for model in models:
        model_df = df[df['model_id'] == model]
        
        # Create confusion matrix
        # We use crosstab and then reindex to ensure all classes are present (even if count is 0)
        cm = pd.crosstab(model_df['ground_truth'], model_df['predicted'])
        cm = cm.reindex(index=classes, columns=classes, fill_value=0)
        
        plt.figure(figsize=(8, 7))
        plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        plt.title(f'Confusion Matrix: {format_model_id(model)}')
        plt.colorbar()
        
        tick_marks = np.arange(len(classes))
        plt.xticks(tick_marks, classes, rotation=45, ha='right')
        plt.yticks(tick_marks, classes)
        
        # Add text annotations
        thresh = cm.max().max() / 2.
        for i in range(len(classes)):
            for j in range(len(classes)):
                val = cm.iloc[i, j]
                plt.text(j, i, str(val),
                         horizontalalignment="center",
                         verticalalignment="center",
                         color="white" if val > thresh else "black")
        
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        
        filename = os.path.join(plots_dir, f'confusion_matrix_{model}.png')
        plt.savefig(filename)
        plt.close()
        print(f"Saved confusion matrix for model '{model}' to {filename}")

def main():
    """Main function to run the analysis and plotting."""
    print("Starting inference analysis...")
    
    df = load_data(EVALUATION_DIR)
    
    if not df.empty:
        os.makedirs(PLOTS_DIR, exist_ok=True)
        
        print("\n--- Generating Gesture Metrics Plots ---")
        plot_gesture_metrics(df, PLOTS_DIR)
        
        print("\n--- Generating Confusion Matrices ---")
        plot_confusion_matrices(df, PLOTS_DIR)
    else:
        print("No valid data found to process.")
        
    print("Analysis complete.")

if __name__ == '__main__':
    main()
