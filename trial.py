import tkinter as tk
from tkinter import messagebox, filedialog

import matplotlib.pyplot as plt
import serial
import threading
from tkinter import *

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from serial.tools import list_ports

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
data1, data2, data3 = [], [], []  # Initialize empty lists for data

# Create line objects for each plot
line1, = ax1.plot([], [], 'r-', label='Sensor 1')
line2, = ax2.plot([], [], 'g-', label='Sensor 2')
line3, = ax3.plot([], [], 'b-', label='Sensor 3')

# Set axis limits
ax1.set_xlim(0, 1000)
ax2.set_xlim(0, 1000)
ax3.set_xlim(0, 1000)

# Set labels and legends
ax1.set_xlabel('Time')
ax1.set_ylabel('Sensor 1 Value')
ax2.set_xlabel('Time')
ax2.set_ylabel('Sensor 2 Value')
ax3.set_xlabel('Time')
ax3.set_ylabel('Sensor 3 Value')
ax1.legend()
ax2.legend()
ax3.legend()

canvas = FigureCanvasTkAgg(fig, master=frm)
canvas.draw()
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Serial communication thread
serial_thread = None  # Initialize serial thread variable
class SerialThread(threading.Thread):
    def __init__(self, serial_port):
        threading.Thread.__init__(self)
        self.serial_port = serial_port
        self.data_queue = []
        self.running = True
        self.paused = False

    def run(self):
        entry_count = 0  # Number of entries recorded
        try:
            while self.running and entry_count != 1001:
                if not self.paused:
                    try:
                        line = self.serial_port.readline().decode().strip()
                        if line:
                            values = line.split(',')
                            if len(values) == 3:
                                sensor1 = int(values[0])
                                sensor2 = int(values[1])
                                sensor3 = int(values[2])
                                print("sensor1: ",sensor1)
                                print("sensor2: ",sensor2)
                                print("sensor3: ",sensor3)
                                data1.append(sensor1)
                                data2.append(sensor2)
                                data3.append(sensor3)

                                entry_count += 1
                    except UnicodeDecodeError:
                        messagebox.showerror("UnicodeDecodeError", "An error occurred while decoding the serial data.")
                        self.resume()
        except serial.SerialException as e:
            messagebox.showerror("SerialException", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if entry_count == 1001:
                print("data1:",data1)
                print("data2:",data2)
                print("data3:",data3)
                Accept_button.configure(state='normal')
                # Call the function to plot the data once data collection is complete
                plot_data()
            self.serial_port.close()  # Close the serial port

    def stop(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

def get_available_ports():
    ports = list_ports.comports()
    return [port.device for port in ports]

def start_serial_communication():
    global serial_thread

    # Get the selected action from the drop-down menu
    selected_action = click_action.get()
    print("Selected Action:", selected_action)

    try:
        # Create and start the serial communication thread
        serial_port = serial.Serial('COM10', 115200)  # Replace 'COM3' with your desired port and baud rate
        serial_thread = SerialThread(serial_port)
        serial_thread.start()

    except serial.SerialException as e:
        messagebox.showerror("SerialException", str(e))

# Associate the start_serial_communication function with the "Start" button click event
Start_button.configure(command=start_serial_communication)

def plot_data():
    # Plot the data once data collection is complete
    ax1.plot(data1, 'r-', label='Sensor 1')

    ax2.plot(data2, 'g-', label='Sensor 2')
    ax3.plot(data3, 'b-', label='Sensor 3')

    # Set axis limits again
    ax1.set_xlim(0, len(data1))
    ax2.set_xlim(0, len(data2))
    ax3.set_xlim(0, len(data3))

    # Update the plot
    canvas.draw()

root.mainloop()
