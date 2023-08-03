from pyfirmata import Arduino

# Replace 'COM3' with the actual port name of your Arduino
arduino_port = 'COM11'

try:
    board = Arduino(arduino_port)

    while True:
        # Read analog values from A0 and A1
        sensor1_value_a0 = board.get_pin('a:0:i').read()
        sensor1_value_a1 = board.get_pin('a:1:i').read()

        # Convert 0-1 range to 0-1023
        if sensor1_value_a0 is not None:
            sensor1_value_a0 *= 1023
            print(f"Sensor 0 (A0) value: {sensor1_value_a0}")
        else:
            print("Sensor 0 (A0) value: None")

        if sensor1_value_a1 is not None:
            sensor1_value_a1 *= 1023
            print(f"Sensor 1 (A1) value: {sensor1_value_a1}")
        else:
            print("Sensor 1 (A1) value: None")

except KeyboardInterrupt:
    print("Exiting...")
except Exception as e:
    print(f"Error: {str(e)}")
