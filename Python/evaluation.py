
import serial
import serial.tools.list_ports
import re
import pandas as pd
import threading
import os
import platform
from datetime import datetime

# --- Configuration ---
BAUD_RATE = 115200
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'Data', 'evaluation')

# --- Globals ---
data_collected = []
stop_thread = False

def find_serial_port():
    """Finds a serial port, prioritizing ST-Link devices."""
    ports = serial.tools.list_ports.comports()
    
    # Keywords to identify the microcontroller
    # Common for ST-Link, but can be expanded
    st_link_keywords = ["st-link", "stmicroelectronics"]

    system = platform.system()
    
    # Check for specific ST-Link ports first
    for port in ports:
        if any(keyword in port.description.lower() or (port.hwid and keyword in port.hwid.lower()) for keyword in st_link_keywords):
            print(f"Found ST-Link device: {port.description} on {port.device}")
            return port.device
            
    # If no ST-Link found, fall back to a generic approach
    if system == "Linux":
        # On Linux, /dev/ttyACMX are common for ST-Link
        for port in ports:
            if "ttyACM" in port.device:
                print(f"Found generic serial port: {port.device}")
                return port.device
    
    # If still nothing, return the first port found, if any
    if ports:
        port = ports[0].device
        print(f"No specific device found. Using the first available port: {port}")
        return port

    return None


def serial_reader(ser):
    """
    Reads from serial port, parses data, and stores it.
    This function runs in a separate thread.
    """
    global data_collected, stop_thread
    print("Starting data recording... Press Enter in the main window to stop.")
    
    while not stop_thread:
        try:
            if ser.in_waiting > 0:
                # Use a larger read to avoid partial lines, but process line by line
                line = ser.readline().decode('utf-8').strip()
                if line:
                    # Regex to parse for inference data
                    match = re.search(r'Inference: ([\d.]+) us \| Class: (.*?) \(Prob: ([\d.]+)\)', line)
                    if match:
                        inference_time = float(match.group(1))
                        classification = match.group(2).strip()
                        probability = float(match.group(3))
                        
                        data_collected.append([inference_time, classification, probability])
                        # Print the original line and append the counter
                        print(f"{line} | Points Collected: {len(data_collected)}")
                    else:
                        # Print non-matching lines (like "Recording...") as they are
                        print(line)

        except serial.SerialException as e:
            print(f"Serial error: {e}")
            break
        except Exception as e:
            # Ignore other potential decoding errors
            pass
            
    print("Data recording stopped.")

def main():
    """ Main function to set up and run the data recorder """
    global stop_thread

    # --- Automatic Port Detection ---
    port_name = find_serial_port()
    if not port_name:
        print("Error: No serial port found. Please ensure your device is connected.")
        return

    # --- Directory and File Setup ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"inference_{timestamp}.csv"
    csv_file_path = os.path.join(DATA_DIR, filename)
    
    print(f"Will save data to: {csv_file_path}")
    os.makedirs(DATA_DIR, exist_ok=True)

    # --- Serial Connection and Threading ---
    try:
        with serial.Serial(port_name, BAUD_RATE, timeout=1) as ser:
            # Flush any old data in the buffer
            ser.reset_input_buffer()
            print(f"Successfully opened port {port_name}.")
            
            # Start the reading thread
            reader_thread = threading.Thread(target=serial_reader, args=(ser,))
            reader_thread.start()
            
            # Wait for user to press Enter
            input() # This will block until Enter is pressed
            
            # Signal the thread to stop
            stop_thread = True
            reader_thread.join() # Wait for the thread to finish

    except serial.SerialException as e:
        print(f"Error opening or reading from serial port: {e}")
        return

    # --- Data Saving ---
    if not data_collected:
        print("No data was collected. Exiting.")
        return

    print(f"\nSaving {len(data_collected)} data points...")
    
    # Create a DataFrame and save to CSV
    df = pd.DataFrame(data_collected, columns=['Inference Time (us)', 'Classification', 'Probability'])
    
    try:
        df.to_csv(csv_file_path, index=False)
        print(f"Data successfully saved to {csv_file_path}")
    except IOError as e:
        print(f"Error saving file: {e}")

if __name__ == '__main__':
    main()
