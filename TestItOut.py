import time

import serial
import numpy as np
import tensorflow as tf


def live(data):
    # Load the TFLite model
    interpreter = tf.lite.Interpreter(model_path="Jash_E1E2E3.tflite")
    interpreter.allocate_tensors()

    # Get input and output details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_shape = (1, 3000, 1)
    output_shape = (1, 6)

    interpreter.resize_tensor_input(input_details[0]['index'], input_shape)
    interpreter.resize_tensor_input(output_details[0]['index'], output_shape)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Define a function to process data through the TFLite model
    def process_data(input_data):
        input_data = np.array([input_data], dtype=np.float32)
        input_data = input_data.reshape(input_data.shape[0], input_data.shape[1], 1)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        return interpreter.get_tensor(output_details[0]['index'])

    # Process data through the TFLite model
    predictions_data = process_data(data)

    # Get the final predicted label
    predicted_label_index = np.argmax(predictions_data)
    actions = ["cylindrical", "hook", "lateral", "palmer", "spherical", "tip"]

    predicted_label = actions[predicted_label_index]
    print(predicted_label)




# Define a function to read data from the sensor
def get_sensor_data(serial_port):
    try:
        line = serial_port.readline().decode().strip()
        values = line.split(',')
        if len(values) == 3:
            return [int(val) for val in values]
        else:
            return None
    except Exception as e:
        print("Error reading data:", e)
        return None


# Main loop
if __name__ == "__main__":
    try:
        # Initialize serial communication and other variables
        serial_port = serial.Serial('COM10', 115200)  # Replace with your settings

        # Initialize TensorFlow Lite interpreter
        interpreter = tf.lite.Interpreter(model_path="New_E3.tflite")
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        # Initialize lists to store data from each sensor
        data1_list = []
        data2_list = []
        data3_list = []

        while True:
            # Read data from the sensor

            sensor_data = get_sensor_data(serial_port)

            if sensor_data is not None:
                # Store data in respective lists
                data1_list.append(sensor_data[0])
                data2_list.append(sensor_data[1])
                data3_list.append(sensor_data[2])

                # Check if data collection is complete
                if len(data1_list) >= 1000 and len(data2_list) >= 1000 and len(data3_list) >= 1000:
                    collected_data=data1_list+data2_list+data3_list
                    print(collected_data)
                    live(collected_data)
                    print("Data collection complete.")
                    print("Data Collecting in 3 second")
                    time.sleep(3)
                    data1_list.clear()
                    data2_list.clear()
                    data3_list.clear()
                    print("")


        # Process and analyze the collected data
        # ...

    except Exception as e:
        print("Error:", e)
    finally:
        if serial_port.is_open:
            serial_port.close()
