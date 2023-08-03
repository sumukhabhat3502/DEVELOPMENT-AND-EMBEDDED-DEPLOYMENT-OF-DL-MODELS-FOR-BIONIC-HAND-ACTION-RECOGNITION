import time
import pyfirmata

# Set the sample frequency and time interval
SAMPLE_RATE = 500
INTERVAL = 1.0 / SAMPLE_RATE

# Define a simple low-pass filter to smooth the data
ALPHA = 0.1

# Create a PyFirmata board object
board = pyfirmata.Arduino('COM10', baudrate=115200)
# Replace 'COM10' with the appropriate port for your Arduino

# Start an iterator thread to avoid buffer overflow
it = pyfirmata.util.Iterator(board)
it.start()

# Define analog input objects for each sensor
analog_input_0 = board.get_pin('a:0:0')
analog_input_1 = board.get_pin('a:1:1')
analog_input_2 = board.get_pin('a:2:2')

# Define a threshold for noisy readings
NOISE_THRESHOLD = 0.02  # Adjust this value based on your sensor characteristics and noise level

# Initialize filtered_data variables with initial values
filtered_data_0 = 0.0
filtered_data_1 = 0.0
filtered_data_2 = 0.0

# Function to apply a simple low-pass filter
def low_pass_filter(prev_value, new_value):
    return prev_value * (1 - ALPHA) + new_value * ALPHA

def main():
    global filtered_data_0, filtered_data_1, filtered_data_2
    while True:
        start_time = time.time()

        # Read raw sensor data
        data_0 = analog_input_0.read()
        data_1 = analog_input_1.read()
        data_2 = analog_input_2.read()

        # Check if the sensor readings are valid (above the noise threshold)
        if data_0 is not None and data_0 > NOISE_THRESHOLD:
            filtered_data_0 = low_pass_filter(filtered_data_0, data_0)
        if data_1 is not None and data_1 > NOISE_THRESHOLD:
            filtered_data_1 = low_pass_filter(filtered_data_1, data_1)
        if data_2 is not None and data_2 > NOISE_THRESHOLD:
            filtered_data_2 = low_pass_filter(filtered_data_2, data_2)

        # Print the filtered data
        print(f"Filtered Data 0: {filtered_data_0:.5f}\tFiltered Data 1: {filtered_data_1:.5f}\tFiltered Data 2: {filtered_data_2:.5f}")

        # Wait for the next interval
        elapsed_time = time.time() - start_time
        time.sleep(max(0, INTERVAL - elapsed_time))

if __name__ == "__main__":
    main()
