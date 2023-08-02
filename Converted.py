import tkinter as tk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
import pandas as pd
import serial
import threading
from matplotlib import animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
from serial.tools import list_ports
import numpy as np
import tensorflow as tf
from pyfirmata import Arduino, util

test_sample = None
arduino_port = 'COM10'  # Replace 'COM3' with the actual port name of your Arduino

root = tk.Tk()
root.geometry("1800x900")
root.resizable(False, False)
root.title("EMG Data")

fontsize = 8
linewidth = 0.75
titlesize = 8
ticklabelsize = 8
plt.rcParams.update({
    "axes.facecolor": "black",
    "lines.linewidth": linewidth,
    "axes.titlesize": titlesize,
    "xtick.labelsize": ticklabelsize,
    "ytick.labelsize": ticklabelsize,
    "figure.figsize": [12.50, 8.20],
    "figure.facecolor": "lightgray"})

click_action = tk.StringVar()
click_action.set("Cylindrical")
Action_menu = tk.OptionMenu(root, click_action, "Cylindrical", "Spherical", "Lateral", "Palmer", "Tip", "Hook")
selected_action = click_action
Action_menu.place(x=8, y=60)
Action_menu.config(width=12)

frmVid = Frame(root, bg='lightgray', width=330, height=400)
frmVid.place(x=20, y=350)
Start_button = Button(root, text="Start", height=4, width=18)
Start_button.place(x=200, y=60)
Accept_button = Button(root, text="Accept Data", height=4, width=18, command=root.destroy)
Accept_button.place(x=1650, y=100)
Reject_button = Button(root, text="Reject Data", height=4, width=18, command=root.destroy)
Reject_button.place(x=1650, y=200)

New_button = Button(root, text="New Data", height=4, width=18, command=root.destroy)
New_button.place(x=1650, y=300)
Close_button = Button(root, text="Close", height=4, width=18, command=root.destroy)
Close_button.place(x=1650, y=500)

frm = Frame(root)
frm.place(x=370, y=400, anchor='w')

# Create three subplots for each sensor
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10))
# Initialize empty lists for data
data1, data2, data3 = [], [], []

# Create line objects for each plot
line1, = ax1.plot([], [], label="Sensor 1")
line2, = ax2.plot([], [], label="Sensor 2")
line3, = ax3.plot([], [], label="Sensor 3")

canvas = FigureCanvasTkAgg(fig, master=frm)
canvas.draw()
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

ax1.set_xlim([0, 100])
ax1.set_ylim(-500, 500)
ax1.plot([], [], "lime")
ax1.grid()
ax1.set_title('Channel 1')

ax2.set_xlim([0, 100])
ax2.set_ylim(-500, 500)
ax2.plot([], [], "lime")
ax2.grid()
ax2.set_title('Channel 2')

ax3.set_xlim([0, 100])
ax3.set_ylim(-500, 500)
ax3.plot([], [], "lime")
ax3.grid()
ax3.set_title('Channel 3')
sensor_names = ["Sensor 1", "Sensor 2", "Sensor 3"]
values_plotted = 0



# Serial communication thread
class SerialThread(threading.Thread):
    def __init__(self, serial_port):
        threading.Thread.__init__(self)
        self.serial_port = serial_port
        self.sensor_values = [None, None, None]  # List to store Sensor1, Sensor2, and Sensor3 values
        self.running = True
        self.paused = False

    def run(self):
        try:
            while self.running:
                if not self.paused:
                    try:
                        # Read data from the Arduino
                        self.sensor_values[0] = self.serial_port.analog[0].read()
                        self.sensor_values[1] = self.serial_port.analog[8].read()
                        self.sensor_values[2] = self.serial_port.digital[32].read()
                    except Exception as e:
                        messagebox.showerror("Error", str(e))
                        self.resume()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.serial_port.exit()  # Close the serial port

    def stop(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def get_values(self):
        return self.sensor_values

# Rest of the code remains the same
serial_thread = None  # Initialize serial thread variable
trial_no = 1  # Initialize trial number
# Dataframe

columns = ([str(i) for i in range(0, 1000)])
columns.extend(["Trial No", "label", "EMG"])
df = pd.DataFrame(columns=columns)


def get_available_ports():
    ports = list_ports.comports()
    return [port.device for port in ports]


def open_port():
    global serial_thread
    if serial_thread is None or not serial_thread.is_alive():
        selected_port = port_menu.get()
        if selected_port:
            # Create serial object
            s = serial.Serial(selected_port, 115200, timeout=5)

            # Create serial thread
            serial_thread = SerialThread(s)
            serial_thread.daemon = True
            serial_thread.start()

        else:
            print("No port selected.")
    else:
        print("Port is already open.")
        serial_thread.resume()  # Resume the serial thread


red_light = None
green_light = None

# Create line objects for the lights
red_light, = ax1.plot([], [], 'ro', markersize=12)
green_light, = ax1.plot([], [], 'go', markersize=12)
plotting_done = False

def update_plot(frame):
    global data1, data2, data3, values_plotted
    global red_light, green_light, plotting_done

    data1 = data1[-1000:]
    data2 = data2[-1000:]
    data3 = data3[-1000:]

    if serial_thread is not None and serial_thread.is_alive():
        # Get data from serial thread
        sensor1_value, sensor2_value, sensor3_value = serial_thread.get_values()
        if sensor1_value is not None and sensor2_value is not None and sensor3_value is not None:
            data1.append(sensor1_value * 1023)  # Convert 0-1 range to 0-1023
            data2.append(sensor2_value * 1023)  # Convert 0-1 range to 0-1023
            data3.append(sensor3_value)

            # Limit the number of data points
            data1 = data1[-1000:]
            data2 = data2[-1000:]
            data3 = data3[-1000:]

            # Update the plot lines with the new data
            line1.set_data(range(len(data1)), data1)
            line2.set_data(range(len(data2)), data2)
            line3.set_data(range(len(data3)), data3)
            values_plotted += 1

        # Update the light colors
        if values_plotted < 1000:
            red_light.set_data([0], [0])
            green_light.set_data([], [])
            plotting_done = False  # Set plotting_done to False
        elif values_plotted > 1100:
            red_light.set_data([], [])
            green_light.set_data([0], [0])
            plotting_done = True  # Set plotting_done to True
            red_light.set_color('red')  # Change marker color to red

    # Rest of the update_plot function remains the same

