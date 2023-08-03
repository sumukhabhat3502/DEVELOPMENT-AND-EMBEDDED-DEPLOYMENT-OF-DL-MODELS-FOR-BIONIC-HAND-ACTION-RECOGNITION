import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import pandas as pd
import serial
import threading
from matplotlib import animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
import pyfirmata

root = tk.Tk()
root.geometry("1800x900")
root.resizable(False, False)
root.title("EMG Data")
arduino_port = 'COM10'  # Replace 'COM10' with the actual port name of your Arduino

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
    def __init__(self, serial_port=None):
        threading.Thread.__init__(self)
        self.serial_port = serial_port
        self.sensor1_value = None
        self.sensor2_value = None
        self.sensor3_value = None
        self.running = True
        self.paused = False

    def run(self):
        try:
            while self.running:
                if not self.paused:
                    try:
                        # Check if the serial port is ready
                        if self.serial_port is not None:
                            # Check the number of analog and digital pins available
                            num_analog_pins = len(self.serial_port.analog)
                            num_digital_pins = len(self.serial_port.digital)

                            if num_analog_pins >= 3:
                                self.sensor1_value = self.serial_port.analog[0].read()
                                self.sensor2_value = self.serial_port.analog[1].read()
                                self.sensor3_value = self.serial_port.analog[2].read()
                                # print(f"Number of analog pins available: {num_analog_pins}")
                                # if num_digital_pins >= 33:
                                    # self.sensor3_value = self.serial_port.digital[32].read()
                                    # print(f"Number of digital pins available: {num_digital_pins}")

                        # Check if the values are valid (not None)
                        if self.sensor1_value is not None:
                            self.sensor1_value *= 1023  # Convert 0-1 range to 0-1023
                            print(f"Sensor 1 value: {self.sensor1_value}")
                        else:
                            print("Sensor 1 value: None")

                        if self.sensor2_value is not None:
                            self.sensor2_value *= 1023  # Convert 0-1 range to 0-1023
                            print(f"Sensor 2 value: {self.sensor2_value}")

                        if self.sensor3_value is not None:
                            self.sensor3_value *= 1023  # Convert 0-1 range to 0-1023
                            print(f"Sensor 3 value: {self.sensor3_value}")
                    except Exception as e:
                        print(f"Error in SerialThread: {str(e)}")
                        self.resume()
        except Exception as e:
            print(f"Error in SerialThread: {str(e)}")
        finally:
            if self.serial_port is not None:
                self.serial_port.exit()  # Close the serial port

    def stop(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def get_values(self):
        return self.sensor1_value, self.sensor2_value, self.sensor3_value


serial_thread = None  # Initialize serial thread variable
trial_no = 1  # Initialize trial number
# Dataframe

columns = ([str(i) for i in range(0, 1000)])
columns.extend(["Trial No", "label", "EMG1", "EMG2", "EMG3"])
df = pd.DataFrame(columns=columns)

def get_available_ports():
    try:
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    except Exception as e:
        print(str(e))
        return []

def open_port():
    global serial_thread
    selected_port = port_menu.get()
    if selected_port:
        if serial_thread is None or not serial_thread.is_alive():
            try:
                # Create serial object
                board = pyfirmata.Arduino(selected_port)
                # Create serial thread
                serial_thread = SerialThread(board)
                serial_thread.daemon = True
                serial_thread.start()
            except Exception as e:
                print(str(e))
        else:
            print("Port is already open.")
            serial_thread.resume()  # Resume the serial thread
    else:
        print("Please select a port.")

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
            data3.append(sensor3_value * 1023)  # Convert 0-1 range to 0-1023

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
    return line1, line2, line3, red_light, green_light

def save_data():
    global trial_no, df, selected_action, values_plotted
    if len(data1) == len(data2) == len(data3) and len(data1) == 1000:
        # Create rows for data1, data2, and data3
        row1 = data1[:1000] + [trial_no, selected_action.get(), "EMG1"]
        row2 = data2[:1000] + [trial_no, selected_action.get(), "EMG2"]
        row3 = data3[:1000] + [trial_no, selected_action.get(), "EMG3"]

        # Append the rows to the dataframe
        df.loc[len(df)] = row1
        df.loc[len(df)] = row2
        df.loc[len(df)] = row3
        trial_no += 1
        values_plotted = 0
        print(df)

    else:
        print("Error: Data arrays have different lengths or are incomplete.")

def on_closing():
    if serial_thread is not None and serial_thread.is_alive():
        serial_thread.stop()
    root.destroy()

def accept_button_click():
    global trial_no, df, selected_action, values_plotted

    name = name_entry.get()
    age = age_entry.get()
    destination_folder = destination_entry.get()

    if name and age and destination_folder:
        if values_plotted > 1100:
            save_data()
            Accept_button.configure(state='disabled')  # Disable the button again until the next trial collection
        else:
            print("Please collect 1000 values before accepting data.")
    else:
        print("Please enter name, age, and select destination folder.")

def reject_button_click():
    print("Data rejected")

def new_button_click():
    root.destroy()

def close_button_click():
    root.destroy()

# Create the animation that updates the plot
ani = animation.FuncAnimation(fig, update_plot, frames=1000, interval=100, blit=True)

def start_button_click():
    try:
        board = pyfirmata.Arduino(arduino_port)
        # Create serial thread
        global serial_thread
        serial_thread = SerialThread(board)
        serial_thread.daemon = True
        serial_thread.start()
        Start_button.configure(state='disabled')
    except Exception as e:
        print(str(e))

def enable_disable_buttons():
    name = name_entry.get()
    age = age_entry.get()
    destination_folder = destination_entry.get()

    if name and age and destination_folder:
        Start_button.configure(state='normal')
        Accept_button.configure(state='normal')
        Reject_button.configure(state='normal')
        Close_button.configure(state='normal')
    else:
        Start_button.configure(state='disabled')
        Accept_button.configure(state='disabled')
        Reject_button.configure(state='disabled')
        Close_button.configure(state='disabled')

def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        destination_entry.delete(0, END)
        destination_entry.insert(0, folder_selected)

name_label = Label(root, text="Name:")
name_label.place(x=20, y=200)
name_entry = Entry(root, width=30)
name_entry.place(x=70, y=200)

age_label = Label(root, text="Age:")
age_label.place(x=270, y=200)
age_entry = Entry(root, width=10)
age_entry.place(x=300, y=200)

destination_entry = Entry(root, width=50)
destination_entry.place(x=28, y=280)
browse_button = Button(root, text="Browse", command=browse_folder)
browse_button.place(x=10, y=280)

name_entry.bind("<KeyRelease>", lambda event: enable_disable_buttons())
age_entry.bind("<KeyRelease>", lambda event: enable_disable_buttons())
destination_entry.bind("<KeyRelease>", lambda event: enable_disable_buttons())

# Create a dropdown list for available ports
port_menu = tk.StringVar(root)
ports = get_available_ports()
port_menu.set(ports[0] if ports else "")  # Set the default selection to the first port if available

Start_button.configure(command=start_button_click)
Accept_button.configure(command=accept_button_click)
Reject_button.configure(command=reject_button_click)
New_button.configure(command=new_button_click)
Close_button.configure(command=close_button_click)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
