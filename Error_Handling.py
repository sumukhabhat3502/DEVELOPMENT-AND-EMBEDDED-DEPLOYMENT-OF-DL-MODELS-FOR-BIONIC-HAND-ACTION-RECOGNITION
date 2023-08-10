import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import os
import matplotlib.pyplot as plt
import pandas as pd
import serial
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
from serial.tools import list_ports
import queue

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

# Entry fields for Name, Age, and Hand
name_label = Label(root, text="Name:")
name_label.place(x=20, y=100)
name_entry = Entry(root)
name_entry.place(x=80, y=100)

age_label = Label(root, text="Age:")
age_label.place(x=20, y=130)
age_entry = Entry(root)
age_entry.place(x=80, y=130)

hand_label = Label(root, text="Hand:")
hand_label.place(x=20, y=160)
hand_entry = Entry(root)
hand_entry.place(x=80, y=160)

# Video Entry
frmVid = Frame(root, bg='lightgray', width=330, height=400)
frmVid.place(x=20, y=350)
Start_button = Button(root, text="Start", height=4, width=18)
Start_button.place(x=200, y=60)
# Save_THRICE=Button(root,text="Save THRICE",height=4,width=18)
# Save_THRICE.place(x=1650,y=0)
Accept_button = Button(root, text="Accept Data", height=4, width=18)
Accept_button.place(x=1650, y=100)
Reject_button = Button(root, text="Reject Data", height=4, width=18, )
Reject_button.place(x=1650, y=200)

# Buttons for each action

# New Data button
New_button = Button(root, text="New Data", height=4, width=18, )
New_button.place(x=1650, y=300)

# Save Data button
Save_button = Button(root, text="Save Data", height=4, width=18)
Save_button.place(x=1650, y=400)

# View Entire Data button
# View_button = Button(root, text="View Entire Data", height=4, width=18)
# View_button.place(x=1650, y=500)

# Ports
ports_dropdown = tk.StringVar()
# Close button
Close_button = Button(root, text="Close", height=4, width=18, command=root.destroy)
Close_button.place(x=1650, y=700)

frm = Frame(root)
frm.place(x=370, y=400, anchor='w')

# Create three subplots for each sensor
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10))
data1, data2, data3 = queue.Queue(maxsize=1000), queue.Queue(maxsize=1000), queue.Queue(maxsize=1000)

# Create line objects for each plot
line1, = ax1.plot([], [], 'r-', label='Sensor 1')
line2, = ax2.plot([], [], 'g-', label='Sensor 2')
line3, = ax3.plot([], [], 'b-', label='Sensor 3')

# Set axis limits
ax1.set_xlim(0, 100)
ax2.set_xlim(0, 100)
ax3.set_xlim(0, 100)

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


# Serial port selection menu
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
            while self.running and entry_count != 1000:
                if not self.paused:
                    try:
                        line = self.serial_port.readline().decode().strip()
                        if line:
                            values = line.split(',')
                            if len(values) == 3:
                                sensor1 = int(values[0])
                                sensor2 = int(values[1])
                                sensor3 = int(values[2])

                                data1.put(sensor1)
                                data2.put(sensor2)
                                data3.put(sensor3)

                                entry_count += 1
                    except UnicodeDecodeError:
                        messagebox.showerror("UnicodeDecodeError", "An error occurred while decoding the serial data.")
                        self.resume()
        except serial.SerialException as e:
            messagebox.showerror("SerialException", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if entry_count == 1000:
                print("Data collection complete.")
                Accept_button.configure(state='normal')
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


ports_menu = tk.OptionMenu(root, ports_dropdown, *get_available_ports())
ports_dropdown.set(get_available_ports()[
                       0] if get_available_ports() else "")  # Set the default selection to the first port if available
ports_menu.place(x=1650, y=600)
ports_menu.config(height=4, width=16)


def start_serial_communication():
    global serial_thread

    # Get the selected action from the drop-down menu
    selected_action = click_action.get()
    print("Selected Action:", selected_action)

    try:
        selected_port = ports_dropdown.get()
        # Create and start the serial communication thread
        serial_port = serial.Serial(selected_port, 115200)  # Replace 'COM3' with your desired port and baud rate
        serial_thread = SerialThread(serial_port)
        serial_thread.start()

    except serial.SerialException as e:
        messagebox.showerror("SerialException", str(e))


# Associate the start_serial_communication function with the "Start" button click event
Start_button.configure(command=start_serial_communication)

# DataFrames for each trial
trial_dataframes = []
columns = ([str(i) for i in range(0, 1000)])
columns.extend(["TrailNumber", "Label", "EMG"])
current_trial_data = pd.DataFrame(columns=columns)

trial_dataframes2 = []
columns2 = ([str(i) for i in range(0, 3000)])
columns2.extend(["TrailNumber", "EMG"])
thrice_data = pd.DataFrame(columns=columns2)

current_trial_number = 1
current_trial_data_thrice = 1


def accept_data():
    global current_trial_data, current_trial_number, current_trial_data_thrice, thrice_data
    # Save the current data to a DataFrame for the current trial
    if not serial_thread or not serial_thread.is_alive():
        row1 = list(data1.queue)
        row1.append(current_trial_number)
        row1.append(selected_action.get())
        row1.append("EMG1")
        row2 = list(data2.queue)
        row2.append(current_trial_number)
        row2.append(selected_action.get())
        row2.append("EMG2")
        row3 = list(data3.queue)
        row3.append(current_trial_number)
        row3.append(selected_action.get())
        row3.append("EMG3")

        current_trial_data.loc[len(current_trial_data)] = row1
        current_trial_data.loc[len(current_trial_data)] = row2
        current_trial_data.loc[len(current_trial_data)] = row3

        # Increment the trial number for the next trial
        current_trial_number += 1

        longrow = list(data1.queue) + list(data2.queue) + list(data3.queue)
        longrow.append(selected_action.get())
        longrow.append("EMG1,EMG2,EMG3")

        thrice_data.loc[len(thrice_data)] = longrow
        # Append the data to the list of trial dataframes
        trial_dataframes.append(current_trial_data_thrice)
        current_trial_data_thrice += 1
        trial_dataframes2.append(thrice_data)

        # Update the plot
        plot_data()

        # Clear the data queues for the next trial
        while not data1.empty():
            data1.get()
        while not data2.empty():
            data2.get()
        while not data3.empty():
            data3.get()

        # Clear the current_trial_data for the next trial
        current_trial_data = pd.DataFrame(columns=columns)
        thrice_data = pd.DataFrame(columns=columns2)
        return
    # Check if data collection is ongoing
    messagebox.showerror("Error", "Data collection is ongoing. Please wait until data collection completes.")


def reject_data():
    if serial_thread and serial_thread.is_alive():
        messagebox.showerror("Error", "Data collection is ongoing. Please wait until data collection completes.")
        return
    # Clear the data queues and update the plot
    while not data1.empty():
        data1.get()
    while not data2.empty():
        data2.get()
    while not data3.empty():
        data3.get()
    plot_data()


def new_data():
    if serial_thread and serial_thread.is_alive():
        messagebox.showerror("Error", "Data collection is ongoing. Please wait until data collection completes.")
        return
    # Clear the trial dataframes and update the plot
    global trial_dataframes, current_trial_data,trial_dataframes2
    trial_dataframes = []
    trial_dataframes2 = []
    current_trial_data = None
    while not data1.empty():
        data1.get()
    while not data2.empty():
        data2.get()
    while not data3.empty():
        data3.get()
    plot_data()


def view_current_trial():
    # Print the current trial dataframe
    print("Current Trial DataFrame:")
    print(current_trial_data)
    return current_trial_data


def view_data():
    combined_data = pd.concat(trial_dataframes)
    print("Combined DataFrame of All Trials:")
    print(combined_data)
    view_data_window = tk.Toplevel(root)
    view_data_window.title("Combined Data")
    view_data_window.geometry("800x600")

    # Create a scrolled text widget to display the data
    text_widget = scrolledtext.ScrolledText(view_data_window, wrap=tk.WORD, width=100, height=30)
    text_widget.insert(tk.END, str(combined_data))
    text_widget.config(state=tk.DISABLED)  # Disable editing of the text widget
    text_widget.pack(fill=tk.BOTH, expand=True)

    # Enable vertical scrolling in the text widget
    text_widget.config(yscrollcommand=True)


def browse_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder_path)


def save_data():
    name = name_entry.get().strip()
    age = age_entry.get().strip()
    hand = hand_entry.get().strip()

    if not name or not age or not hand:
        messagebox.showerror("Error", "Please enter Name, Age, and Hand before saving data.")
        return

    combined_data = pd.concat(trial_dataframes)

    # Get the destination folder from the Entry widget
    destination_folder = folder_entry.get().strip()
    if not destination_folder:
        messagebox.showerror("Error", "Please select a destination folder.")
        return

    # Create the folder if it doesn't exist
    os.makedirs(destination_folder, exist_ok=True)

    filename = os.path.join(destination_folder, f"{name}_{age}_{hand}.csv")
    combined_data.to_csv(filename, index=False)
    messagebox.showinfo("Data Saved", f"Data has been saved to {filename} successfully!")


def save_thrice():
    if serial_thread and serial_thread.is_alive():
        messagebox.showerror("Error", "Data collection is ongoing. Please wait until data collection completes.")
        return
    name = name_entry.get().strip()
    age = age_entry.get().strip()
    hand = hand_entry.get().strip()

    if not name or not age or not hand:
        messagebox.showerror("Error", "Please enter Name, Age, and Hand before saving data.")
        return

    thrice_data = pd.concat(trial_dataframes2)

    # Get the destination folder from the Entry widget
    destination_folder = folder_entry.get().strip()
    if not destination_folder:
        messagebox.showerror("Error", "Please select a destination folder.")
        return

    # Create the folder if it doesn't exist
    os.makedirs(destination_folder, exist_ok=True)

    another = "another"
    filename2 = os.path.join(destination_folder, f"{name}_{age}_{hand}_{another}.csv")
    thrice_data.to_csv(filename2, index=False)
    messagebox.showinfo("Data Saved", f"Data has been saved to {filename2} successfully!")


# Entry field for the destination folder
folder_label = Label(root, text="Destination Folder:")
folder_label.place(x=20, y=250)
folder_entry = Entry(root, width=30)
folder_entry.place(x=150, y=250)
browse_button = Button(root, text="Browse", command=browse_folder)
browse_button.place(x=20, y=300)


def are_fields_filled():
    name = name_entry.get().strip()
    hand = hand_entry.get().strip()
    folder = folder_entry.get().strip()
    return name and hand and folder


def enable_buttons():
    if are_fields_filled():
        Start_button.configure(state='normal')
        Accept_button.configure(state='normal')
        Reject_button.configure(state='normal')
        New_button.configure(state='normal')
        Save_button.configure(state='normal')
    else:
        Start_button.configure(state='disabled')
        Accept_button.configure(state='disabled')
        Reject_button.configure(state='disabled')
        New_button.configure(state='disabled')
        Save_button.configure(state='disabled')


# Bind the Entry fields to the enable_buttons function
name_entry.bind("<KeyRelease>", lambda event: enable_buttons())
hand_entry.bind("<KeyRelease>", lambda event: enable_buttons())
folder_entry.bind("<KeyRelease>", lambda event: enable_buttons())


def plot_data():
    ax1.clear()
    ax2.clear()
    ax3.clear()

    # Plot the data once data collection is complete
    ax1.plot(list(data1.queue), 'r-', label='Sensor 1')
    ax2.plot(list(data2.queue), 'g-', label='Sensor 2')
    ax3.plot(list(data3.queue), 'b-', label='Sensor 3')

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

    # Update the plot
    canvas.draw()


# ani = animation.FuncAnimation(fig, animate, interval=100, blit=True)
Accept_button.configure(command=accept_data)
New_button.configure(command=new_data)
Reject_button.configure(command=reject_data)
Save_button.configure(command=save_thrice)
# Save_THRICE.configure(command=save_thrice)
# View_button.configure(command=view_data)


root.mainloop()
