
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
        'rf': 'RF',
        'svm': 'SVM'
    }
    parts = model_id.split('_')
    if len(parts) == 2:
        trainer, model_type = parts
        return f"{label_map.get(trainer, trainer)} {label_map.get(model_type, model_type)}"
    return model_id # fallback

def plot_gesture_metrics(df, plots_dir):
    """
    Creates bar charts for each gesture comparing models (Accuracy only).
    """
    gestures = df['ground_truth'].unique()
    
    # Define color palette (MLP=Blues, RF=Greens, SVM=Orange)
    color_map = {
        'ne_mlp': '#1f77b4', # Dark Blue
        'hm_mlp': '#aec7e8', # Light Blue
        'ne_rf':  '#2ca02c', # Dark Green
        'hm_rf':  '#98df8a', # Light Green
        'ne_svm': '#ff7f0e', # Orange
    }
    
    # Define desired order
    desired_order = ['ne_mlp', 'hm_mlp', 'ne_rf', 'hm_rf', 'ne_svm']

    for gesture in gestures:
        print(f"\nStats for Gesture: {gesture}")
        gesture_df = df[df['ground_truth'] == gesture]
        
        unique_models = gesture_df['model_id'].unique()
        models = sorted(unique_models, key=lambda x: desired_order.index(x) if x in desired_order else 999)
        
        acc_means, acc_cis = [], []
        
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
            
            print(f"  - {format_model_id(model):<20}: Acc={acc:.2%}")

        # --- Plotting ---
        plt.figure(figsize=(8, 6))
        
        x_pos = np.arange(len(models))
        model_labels = [format_model_id(m) for m in models]
        
        bar_colors = [color_map.get(m, '#7f7f7f') for m in models]
        
        # Accuracy Plot
        plt.bar(x_pos, acc_means, yerr=acc_cis, capsize=5, color=bar_colors, alpha=0.9, edgecolor='black', linewidth=0.5)
        plt.xticks(x_pos, model_labels, rotation=45, ha='right')
        plt.ylabel('Accuracy')
        plt.ylim(0, 1.1)
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        
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

def plot_overall_metrics(df, plots_dir):
    """
    Creates bar charts for overall performance comparing models (Accuracy & Time).
    """
    print("\n--- Generating Overall Metrics Plot ---")
    
    # Define desired order
    desired_order = ['ne_mlp', 'hm_mlp', 'ne_rf', 'hm_rf', 'ne_svm']
    
    unique_models = df['model_id'].unique()
    # Sort models based on desired_order, putting unknown ones at the end
    models = sorted(unique_models, key=lambda x: desired_order.index(x) if x in desired_order else 999)
    
    # Define color palette (MLP=Blues, RF=Greens, SVM=Orange)
    color_map = {
        'ne_mlp': '#1f77b4', # Dark Blue
        'hm_mlp': '#aec7e8', # Light Blue
        'ne_rf':  '#2ca02c', # Dark Green
        'hm_rf':  '#98df8a', # Light Green
        'ne_svm': '#ff7f0e', # Orange
    }
    
    bar_colors = [color_map.get(m, '#7f7f7f') for m in models]
    
    acc_means, acc_cis = [], []
    time_means, time_cis = [], []
    
    for model in models:
        model_data = df[df['model_id'] == model]
        
        # --- Accuracy Stats ---
        is_correct = (model_data['predicted'] == model_data['ground_truth']).astype(int)
        acc = np.mean(is_correct)
        n = len(is_correct)
        # 95% CI for proportion (Wald interval)
        acc_ci = 1.96 * np.sqrt((acc * (1 - acc)) / n) if n > 0 else 0
        
        acc_means.append(acc)
        acc_cis.append(acc_ci)
        
        # --- Time Stats ---
        times = model_data['Inference Time (us)']
        t_mean = np.mean(times)
        t_sem = st.sem(times)
        # 95% CI for mean
        t_ci = t_sem * st.t.ppf((1 + 0.95) / 2., len(times)-1) if len(times) > 1 else 0
        
        time_means.append(t_mean)
        time_cis.append(t_ci)

    # --- Plotting ---
    x_pos = np.arange(len(models))
    model_labels = [format_model_id(m) for m in models]
    
    # 1. Accuracy Plot
    plt.figure(figsize=(8, 6))
    plt.bar(x_pos, acc_means, yerr=acc_cis, capsize=5, color=bar_colors, alpha=0.9, edgecolor='black', linewidth=0.5)
    plt.xticks(x_pos, model_labels, rotation=45, ha='right')
    plt.ylabel('Overall Accuracy')
    plt.ylim(0, 1.1)
    plt.title('Overall Accuracy per Model')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    acc_filename = os.path.join(plots_dir, 'overall_accuracy.png')
    plt.savefig(acc_filename)
    plt.close()
    print(f"Saved overall accuracy plot to {acc_filename}")

    # 2. Time Plot
    plt.figure(figsize=(8, 6))
    plt.bar(x_pos, time_means, yerr=time_cis, capsize=5, color=bar_colors, alpha=0.9, edgecolor='black', linewidth=0.5)
    plt.xticks(x_pos, model_labels, rotation=45, ha='right')
    plt.ylabel('Average Inference Time (us)')
    plt.title('Overall Inference Time per Model')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    time_filename = os.path.join(plots_dir, 'overall_inference_time.png')
    plt.savefig(time_filename)
    plt.close()
    print(f"Saved overall inference time plot to {time_filename}")

def print_overall_metrics(df):
    """
    Prints the overall accuracy and inference time for each model across all gestures.
    """
    print("\n=== Overall Model Performance ===")
    models = sorted(df['model_id'].unique())
    
    # Header
    print(f"{'Model':<25} | {'Accuracy':<10} | {'Avg Time (us)':<15}")
    print("-" * 56)

    for model in models:
        model_df = df[df['model_id'] == model]
        
        # Accuracy
        is_correct = (model_df['predicted'] == model_df['ground_truth']).astype(int)
        acc = np.mean(is_correct)
        
        # Time
        times = model_df['Inference Time (us)']
        t_mean = np.mean(times)
        
        print(f"{format_model_id(model):<25} | {acc:.2%}     | {t_mean:.2f}")
    print("=================================\n")

def main():
    """Main function to run the analysis and plotting."""
    print("Starting inference analysis...")
    
    df = load_data(EVALUATION_DIR)
    
    if not df.empty:
        os.makedirs(PLOTS_DIR, exist_ok=True)
        
        print_overall_metrics(df)
        
        print("\n--- Generating Gesture Metrics Plots ---")
        plot_gesture_metrics(df, PLOTS_DIR)
        plot_overall_metrics(df, PLOTS_DIR)
        
        print("\n--- Generating Confusion Matrices ---")
        plot_confusion_matrices(df, PLOTS_DIR)
    else:
        print("No valid data found to process.")
        
    print("Analysis complete.")

if __name__ == '__main__':
    main()
