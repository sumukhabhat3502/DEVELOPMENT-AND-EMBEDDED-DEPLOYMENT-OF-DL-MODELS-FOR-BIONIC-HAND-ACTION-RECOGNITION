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
values_plotted=0
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
            while self.running and entry_count != 1100:
                if not self.paused:
                    try:
                        line = self.serial_port.readline().decode().strip()
                        # print(line)
                        if line:
                            values = line.split(',')
                            if len(values) == 3:
                                sensor1 = int(values[0])
                                sensor2 = int(values[1])
                                sensor3 = int(values[2])
                                self.data_queue.append((sensor1, sensor2, sensor3))
                                entry_count += 1
                        # print("sensor_queue")
                        # print(self.data_queue)
                    except UnicodeDecodeError:
                        messagebox.showerror("UnicodeDecodeError", "An error occurred while decoding the serial data.")
                        self.resume()
        except serial.SerialException as e:
            messagebox.showerror("SerialException", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            # print(entry_count)
            if entry_count == 1100:
                Accept_button.configure(state='normal')
            self.serial_port.close()  # Close the serial port

    def stop(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def get_data(self):
        data = self.data_queue.copy()
        self.data_queue.clear()
        return data



trial_no = 1  # Initialize trial number
#Dataframe

columns=([str(i) for i in range(0, 1000)])
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

    # data1 = data1[-1000:]
    # data2 = data2[-1000:]
    # data3 = data3[-1000:]

    if serial_thread is not None and serial_thread.is_alive():
        # Get data from serial thread
        new_data = serial_thread.get_data()
        # print("new data")
        print("new_data: ",new_data)

        # print(len(new_data))

        # Process new data
        for sensor1, sensor2, sensor3 in new_data:
            data1.append(sensor1)
            data2.append(sensor2)
            data3.append(sensor3)

        # Limit the number of data points
        data1 = data1[-1000:]
        data2 = data2[-1000:]
        data3 = data3[-1000:]

        # Update the plot lines with the new data for each sensor
        line1.set_data(range(len(data1)), data1)
        line2.set_data(range(len(data2)), data2)
        line3.set_data(range(len(data3)), data3)
        values_plotted += len(new_data)

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
    # print(new_data)
    return line1, line2, line3, red_light, green_light

def save_data():
    global trial_no, df, selected_action, values_plotted
    if len(data1) == len(data2) == len(data3) and len(data1) == 1000:
        # Create rows for data1, data2, and data3
        row1 = (data1[:1000])
        row1.extend([trial_no, selected_action.get(), "EMG1"])
        row2 = (data2[:1000])
        row2.extend([trial_no, selected_action.get(), "EMG2"])
        row3 = (data3[:1000])
        row3.extend([trial_no, selected_action.get(), "EMG3"])

        # Append the rows to the dataframe
        df.loc[len(df)] = row1
        df.loc[len(df)] = row2
        df.loc[len(df)] = row3
        trial_no += 1
        values_plotted = 0
        print(df)
        # df.to_csv("emg_data.csv", index=False)
        # Get the name and age entered by the user
        name = name_entry.get()
        age = age_entry.get()

        # Get the destination folder
        destination_folder = destination_entry.get()

        if name and age and destination_folder:
            # Create the file name with name and age
            file_name = f"{name}_{age}.csv"

            # Combine the destination folder and file name
            file_path = f"{destination_folder}/{file_name}"

            # Save the dataframe to the CSV file
            df.to_csv(file_path, index=False)
            print(f"Data saved to: {file_path}")
        else:
            messagebox.showerror("Error", "Please enter name, age, and select destination folder.")

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
            messagebox.showerror("Error", "Please collect 1000 values before accepting data.")
    else:
        messagebox.showerror("Error", "Please enter name, age, and select destination folder.")

def reject_button_click():
    messagebox.showinfo("Data Rejected", "Data rejected")

def new_button_click():
    # enable_buttons()
    root.destroy()

def close_button_click():
    # enable_buttons()
    root.destroy()

# Create the animation that updates the plot
ani = animation.FuncAnimation(fig, update_plot, frames=1000, interval=100, blit=True)

def start_button_click():
    try:
        open_port()
    except serial.SerialException as e:
        messagebox.showerror("SerialException", str(e))
    except Exception as e:
        messagebox.showerror("Error", str(e))
        # enable_buttons()

# Function to enable or disable buttons based on the presence of values in name, age, and destination folder fields
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


# Function to browse and select the destination folder
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

#Entry field to display the selected destination folder
destination_entry = Entry(root, width=50)
destination_entry.place(x=28
                        , y=280)
browse_button = Button(root, text="Browse", command=browse_folder)
browse_button.place(x=10, y=280)

# Bind the enable_disable_buttons function to the entry fields
name_entry.bind("<KeyRelease>", lambda event: enable_disable_buttons())
age_entry.bind("<KeyRelease>", lambda event: enable_disable_buttons())
destination_entry.bind("<KeyRelease>", lambda event: enable_disable_buttons())


# Create a dropdown list for available ports
port_menu = tk.StringVar(root)
ports = get_available_ports()
port_menu.set(ports[0] if ports else "")  # Set the default selection to the first port if available
port_dropdown = OptionMenu(root, port_menu, *ports)
port_dropdown.place(x=1650, y=300)
port_dropdown.config(height = 4, width=16)

Start_button.configure(command=start_button_click)
Accept_button.configure(command=accept_button_click)
Reject_button.configure(command=reject_button_click)
New_button.configure(command=new_button_click)
Close_button.configure(command=close_button_click)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()





