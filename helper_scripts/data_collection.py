import serial
import serial.tools.list_ports
import threading
import csv
import time
import os
import platform
from datetime import datetime

# ================= CONFIGURATION =================
# Replace these defaults if your setup differs
DEFAULT_WINDOWS_PORT = 'COM3'
DEFAULT_LINUX_PORT = '/dev/ttyACM0'
SAMPLE_LABELS = [
    "Accel_X", "Accel_Y", "Accel_Z",
    "Gyro_X", "Gyro_Y", "Gyro_Z",
    "Mag_X", "Mag_Y", "Mag_Z",
]

def _detect_default_port():
    system = platform.system().lower()
    if 'windows' in system:
        return DEFAULT_WINDOWS_PORT
    if 'linux' in system:
        return DEFAULT_LINUX_PORT
    return DEFAULT_WINDOWS_PORT

SERIAL_PORT = _detect_default_port()
BAUD_RATE = 115200
OUTPUT_DIR = "../runs"  # Directory to save files in
# =================================================

# Global variables to manage state
data_runs = []  # List of runs. Each run is a list of 9-value samples
current_run_index = -1
is_recording = True

def read_serial_data():
    """Background thread function to read from serial port."""
    global current_run_index, data_runs
    
    try:
        # Open serial port
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Successfully connected to {SERIAL_PORT}")
            print("Waiting for data... (Press Nucleo Button to send)")

            while is_recording:
                if ser.in_waiting > 0:
                    try:
                        # Read line, decode, and strip whitespace
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        
                        if not line:
                            continue

                        if line == "NEW_RUN":
                            # Start a new run list
                            data_runs.append([]) 
                            current_run_index += 1
                            print(f"\n---> Detected NEW_RUN (Run #{current_run_index + 1})")
                        
                        else:
                            # Attempt to parse a full sensor sample
                            parts = [p.strip() for p in line.split(',')]
                            if len(parts) == len(SAMPLE_LABELS) and current_run_index >= 0:
                                try:
                                    sample = [int(p) for p in parts]
                                except ValueError:
                                    continue
                                data_runs[current_run_index].append(sample)
                                # Optional: Print a dot to show activity without spamming
                                print(".", end="", flush=True)
                                
                    except ValueError:
                        # Ignore lines that aren't valid data (garbage or partial lines)
                        continue
                        
    except serial.SerialException as e:
        print(f"\nError opening serial port: {e}")

def save_to_csv():
    """Aligns data columns and saves to CSV in the specified directory."""
    if not data_runs:
        print("\nNo data recorded.")
        return

    # 1. Create the directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        print(f"\nCreating directory: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)

    # 2. Generate filename with timestamp and path
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(OUTPUT_DIR, f"recording_{timestamp}.csv")

    # Determine the maximum number of rows needed (longest run)
    max_length = max(len(run) for run in data_runs)
    
    # Create headers: Run1_Accel_X, ..., Run2_Mag_Z, ...
    headers = []
    for i in range(len(data_runs)):
        headers.extend([f"Run{i+1}_{label}" for label in SAMPLE_LABELS])

    print(f"\n\nSaving {len(data_runs)} runs to {filename}...")

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        # Write data row by row
        for i in range(max_length):
            row = []
            for run in data_runs:
                if i < len(run):
                    # If this run has data at this index, add it
                    row.extend(run[i])
                else:
                    # If this run is shorter, pad with empty strings
                    row.extend([""] * len(SAMPLE_LABELS))
            writer.writerow(row)
            
    print("Done!")

if __name__ == "__main__":
    # 1. Select Port (Optional auto-detection or use config)
    print("Available Ports:")
    ports = serial.tools.list_ports.comports()
    for p in ports:
        print(f" - {p.device} ({p.description})")
    
    print(f"\nAttempting to connect to {SERIAL_PORT}...")
    
    # 2. Start the serial reading in a separate thread
    serial_thread = threading.Thread(target=read_serial_data)
    serial_thread.start()

    # 3. Wait for user input to stop
    input("\nPRESS ENTER TO STOP RECORDING AND SAVE...\n")
    
    # 4. Stop thread and save
    is_recording = False
    serial_thread.join()
    save_to_csv()
