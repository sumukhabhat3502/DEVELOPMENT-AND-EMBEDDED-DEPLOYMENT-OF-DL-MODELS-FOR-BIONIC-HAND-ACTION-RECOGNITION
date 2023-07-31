# tkinter imports
import tkinter as tk
from tkinter.ttk import Progressbar
from tkinter import *
from tkinter import filedialog as fdcd, filedialog, messagebox

import os
import time
from prettytable import PrettyTable
import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score
from tensorflow import keras
from sklearn.model_selection import KFold
from sklearn.preprocessing import LabelEncoder
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import Conv1D, Dropout, MaxPooling1D, Flatten, Dense
from matplotlib import pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Global variables
# Datasets definition
dataset = None
x, y = None, None
ex, ey = None, None
model = None
user_model_name = ""
unique_labels_emg1 = None
unique_labels_emg2 = None
unique_labels_emg3 = None
cmodel = None
sensor_dataset = None

# single action x and y
sx, sy = None, None


# Error display box
def display_error(message):
    # Display an error popup window
    messagebox.showerror("Error", message)


# Function Definitions
def import_data():
    global dataset, unique_labels_emg1, unique_labels_emg2, unique_labels_emg3
    try:
        filename = fdcd.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        dataset = pd.read_csv(filename)
        # Get unique labels and their counts for each EMG sensor
        unique_labels_emg1 = dataset.loc[dataset['EMG'] == 'EMG1', 'label'].value_counts()
        unique_labels_emg2 = dataset.loc[dataset['EMG'] == 'EMG2', 'label'].value_counts()
        unique_labels_emg3 = dataset.loc[dataset['EMG'] == 'EMG3', 'label'].value_counts()

        # Create a PrettyTable object
        table = PrettyTable()
        table.field_names = ["", "EMG1", "EMG2", "EMG3"]
        # Get unique labels from all EMG sensors
        labels = set(unique_labels_emg1.index) | set(unique_labels_emg2.index) | set(unique_labels_emg3.index)
        # Add rows to the table
        for label in labels:
            row = [label, unique_labels_emg1.get(label, 0), unique_labels_emg2.get(label, 0),
                   unique_labels_emg3.get(label, 0)]
            table.add_row(row)
        # Display the label information as a table
        label_info = str(table)
        label_info_label.config(text=label_info)
    except Exception as e:
        display_error(f"Error occurred while importing data: {e}")


def get_emg_data(sensor_name):
    # shall provide us with x and y parameters/data
    global x, y, sensor_dataset
    dataset_features_ch1 = dataset[dataset['EMG'] == sensor_name]
    sensor_dataset = dataset_features_ch1
    dataset_labels = dataset_features_ch1['label']
    dataset_features = dataset_features_ch1.drop(columns=['label', 'EMG'], axis=1)
    encoder = LabelEncoder()
    encoder.fit(dataset_labels)
    encoded_y = encoder.transform(dataset_labels)
    y = to_categorical(encoded_y)
    x = np.array(dataset_features[:])
    x = x.reshape(x.shape[0], x.shape[1], 1)
    x = np.asarray(x).astype(np.float32)
    # displaying that sensors stats only
    # Create a PrettyTable object
    table = PrettyTable()
    table.field_names = ["", sensor_name]
    labels = set(unique_labels_emg1.index)
    sensor_stats = None
    if sensor_name == "EMG1":
        sensor_stats = unique_labels_emg1
    elif sensor_name == "EMG2":
        sensor_stats = unique_labels_emg2
    elif sensor_name == "EMG3":
        sensor_stats = unique_labels_emg3
    # we are displaying that sensors stats only
    for label in labels:
        row = [label, sensor_stats.get(label, 0)]
        table.add_row(row)

    label_selected_sensor = str(table)
    sensor_info_label.config(text=label_selected_sensor)


def get_multi_emg_data(sensor1, sensor2):
    global x, y, sensor_dataset
    dataset_features_multi = dataset[(dataset['EMG'] == sensor1) | (dataset['EMG'] == sensor2)]
    sensor_dataset = dataset_features_multi
    dataset_labels = dataset_features_multi['label']
    dataset_features = dataset_features_multi.drop(columns=['label', 'EMG'], axis=1)
    encoder = LabelEncoder()
    encoder.fit(dataset_labels)
    encoded_y = encoder.transform(dataset_labels)
    y = to_categorical(encoded_y)
    x = np.array(dataset_features[:])
    x = x.reshape(x.shape[0], x.shape[1], 1)
    x = np.asarray(x).astype(np.float32)

    table = PrettyTable()
    table.field_names = ["", sensor1, sensor2]
    labels = set(unique_labels_emg1.index) | set(unique_labels_emg2.index)
    sensor1_stats = unique_labels_emg1
    sensor2_stats = unique_labels_emg2
    for label in labels:
        row = [label, sensor1_stats.get(label, 0), sensor2_stats.get(label, 0)]
        table.add_row(row)

    label_selected_sensor = str(table)
    sensor_info_label.config(text=label_selected_sensor)


def single_action_eval_results_tf():
    global sx, sy, cmodel
    actions = ["cylindrical", "hook", "lateral", "palmer", "spherical", "tip"]
    table = PrettyTable(["Action", "Accuracy", "Execution Time"])

    for action in actions:
        # Prepare input data for the current action
        data = sensor_dataset[sensor_dataset['label'] == action]
        data_features = data.drop(columns=['label', 'EMG'], axis=1)
        data_labels = data['label']
        encoder = LabelEncoder()
        encoder.fit(data_labels)
        encoded_y = encoder.transform(data_labels)
        sy = to_categorical(encoded_y, num_classes=6)
        sx = np.array(data_features[:])
        sx = sx.reshape(sx.shape[0], sx.shape[1], 1)
        print(sx.shape)
        print(sy.shape)

        interpreter = tf.lite.Interpreter(model_path=cmodel)
        interpreter.allocate_tensors()

        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        input_shape = input_details[0]['shape'][1:]  # Get the expected input shape of the model

        # Check if the input shape matches the expected shape of the model
        if not np.array_equal(sx.shape[1:], input_shape):
            print(f"Resizing input tensor for action '{action}' to match the TFLite model input shape.")
            interpreter.resize_tensor_input(input_details[0]['index'], sx.shape)
            interpreter.allocate_tensors()
            input_details = interpreter.get_input_details()

        # Convert sx to float32 and add batch dimension of size 1
        sx = np.asarray([sx], dtype=np.float32)

        interpreter.set_tensor(input_details[0]['index'], sx)
        interpreter.invoke()
        tflite_model_predictions = interpreter.get_tensor(output_details[0]['index'])

        prediction_classes = np.argmax(tflite_model_predictions, axis=1)
        true_labels = np.argmax(sy, axis=1)

        acc = accuracy_score(prediction_classes, true_labels) * 100

        table.add_row([action, f"{acc:.2f}%", "N/A"])

    # Display the results in the label
    single_action_evaluation_tf.config(text=f"Model Evaluation:\n{table}")


def single_action_eval_metric():
    global sensor_dataset, dataset, model, sx, sy
    actions = ["cylindrical", "hook", "lateral", "palmer", "spherical",
               "tip"]
    table = PrettyTable(["Action", "Accuracy", "Execution Time"])

    data = sensor_dataset

    for action in actions:
        data = data[data['label'] == action]
        data_features = data.drop(columns=['label', 'EMG'], axis=1)
        data_labels = data['label']
        encoder = LabelEncoder()
        encoder.fit(data_labels)
        encoded_y = encoder.transform(data_labels)

        # Convert encoded_y to one-hot encoded format
        sy = to_categorical(encoded_y, num_classes=6)  # Assuming there are 6 classes
        sx = np.array(data_features[:])
        sx = sx.reshape(sx.shape[0], sx.shape[1], 1)
        sx = np.asarray(sx).astype(np.float32)
        if model is not None:
            start_time = time.time()
            loaded_model = keras.models.load_model(model)
            loss, acc = loaded_model.evaluate(x, y, verbose=2)
            end_time = time.time()
            execution_time = end_time - start_time
            table.add_row([action, f"{acc * 100:.2f}%", f"{execution_time:.2f} sec"])
        else:
            messagebox.showwarning("No Model", "Please import a model first!")
            break
        table_str = str(table)
        single_action_evaluation.config(text=table_str)


def on_select_option(*args):
    selected_option = click_action.get()
    if selected_option == "Only EMG1":
        get_emg_data('EMG1')
    elif selected_option == "Only EMG2":
        get_emg_data('EMG2')
    elif selected_option == "Only EMG3":
        get_emg_data('EMG3')
    elif selected_option == "Only EMG1 and EMG2":
        get_multi_emg_data('EMG1', 'EMG2')
    else:
        pass


def display_empty_progress_bar():
    progress_bar = Progressbar(root, length=490, mode='determinate')
    progress_bar.place(x=290, y=60)
    progress_bar['value'] = 0
    progress_bar.update()
    return progress_bar


def train_data():
    global x, y
    if user_model_name == '':
        display_error(f"You must provide the user model name before training the model")
        return

    try:
        kfold = KFold(n_splits=3, shuffle=True)
        model = Sequential()
        model.add(Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=(x.shape[1], 1)))
        model.add(Conv1D(filters=64, kernel_size=3, activation='relu'))
        model.add(Dropout(0.5))
        model.add(MaxPooling1D(pool_size=2))
        model.add(Flatten())
        model.add(Dense(100, activation='relu'))
        model.add(Dense(y.shape[1], activation='softmax'))
        model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

        fold_no = 1
        Results = {'accuracy': [], 'loss': [], 'val_accuracy': [], 'val_loss': []}
        # Create progress bar
        progress = display_empty_progress_bar()
        progress.update()

        for train, test in kfold.split(x, y):
            print('------------------------------------------------------------------------')
            print(f"Training for fold {fold_no} ...")
            history = model.fit(x[train], y[train], epochs=100, batch_size=100, verbose=1,
                                validation_data=(x[test], y[test]))

            fold_no = fold_no + 1
            Results['accuracy'].append(history.history['accuracy'])
            Results['loss'].append(history.history['loss'])
            Results['val_accuracy'].append(history.history['val_accuracy'])
            Results['val_loss'].append(history.history['val_loss'])

            # Update progress bar in GUI
            progress['value'] += 33.3333333
            root.update()

        model.save(f"{user_model_name}.h5")

        A = Results['accuracy']
        B = Results['val_accuracy']
        C = Results['loss']
        D = Results['val_loss']

        TrainAcc = np.concatenate((A[0], A[1], A[2]), axis=0)
        TestAcc = np.concatenate((B[0], B[1], B[2]), axis=0)
        Trainloss = np.concatenate((C[0], C[1], C[2]), axis=0)
        Testloss = np.concatenate((D[0], D[1], D[2]), axis=0)

        # Plotting cumulative graph
        plot_training_graph(TrainAcc, TestAcc, Trainloss, Testloss)

    except Exception as e:
        display_error(f"Import the csv file and emg data first \nError occurred during model training: {e}")


def plot_training_graph(TrainAcc, TestAcc, Trainloss, Testloss):
    fig, (ax1, ax2) = plt.subplots(2, 1)
    plt.subplots_adjust(left=0.1,
                        bottom=0.2,
                        right=0.9,
                        top=1.0,
                        wspace=0.6,
                        hspace=0.6)
    fig.set_figheight(5)
    fig.set_figwidth(5)
    ax1.plot(TrainAcc, 'b')
    ax1.plot(TestAcc, 'r-')
    ax1.set_ylim(-0.2, 1.2)
    ax1.set_title('Model Accuracy')
    ax1.set(xlabel='Epochs', ylabel='Accuracy')
    ax1.legend(['Train Accuracy', 'Test Accuracy'], loc='lower right')
    ax2.plot(Trainloss, 'b')
    ax2.plot(Testloss, 'r-')
    ax2.set_title('Model Loss')
    ax2.set(xlabel='Epochs', ylabel='Loss')
    ax2.legend(['Train Loss', 'Test Loss'], loc='upper right')

    for widget in frm3.winfo_children():
        widget.destroy()

    # Embedding the matplotlib figure in the tkinter frame
    canvas = FigureCanvasTkAgg(fig, master=frm3)
    canvas.draw()
    canvas.get_tk_widget().pack()

    # Optional: Add a toolbar for the plot
    toolbar = NavigationToolbar2Tk(canvas, frm3)
    toolbar.update()
    canvas.get_tk_widget().pack()

    # Optional: Add a button to save the plot
    save_button = Button(frm3, text="Save Plot", command=save_plot)
    save_button.pack()


def save_plot():
    # Save the plot as an image file
    filetypes = [('PNG Image', '*.png'), ('JPEG Image', '*.jpg'), ('All Files', '*.*')]
    filename = fdcd.asksaveasfilename(filetypes=filetypes, defaultextension='.png')
    if filename:
        plt.savefig(filename)
        messagebox.showinfo("Save Plot", "Plot saved successfully!")


def import_model():
    global model
    try:
        filename = fdcd.askopenfilename(filetypes=[("H5 Files", "*.h5")])
        model = filename
        file_size = os.path.getsize(filename)
        size_in_mb = file_size / (1024 * 1024)  # Convert to MB
        messagebox.showinfo("Loaded Model", "Model has been loaded successfully!")
        load_model_label.config(text=f"File Name: {os.path.basename(filename)} \n File size: {size_in_mb:.2f} mb")
    except Exception as e:
        display_error(f"Error occurred during importing the model: {e}\n Try choosing the path to the model")


def evaluate_model():
    global model, x, y
    if model is not None:
        start_time = time.time()
        loaded_model = keras.models.load_model(model)
        loss, acc = loaded_model.evaluate(x, y, verbose=2)
        end_time = time.time()
        execution_time = end_time - start_time
        evaluate_model_label.config(
            text=f"Model Evaluation:\nModel Accuracy: {acc * 100:.2f}% \n Execution Time: {execution_time:.2f} sec")
    else:
        messagebox.showwarning("No Model", "Please import a model first!")
    single_action_eval_metric()


def load_cmodel():
    global cmodel
    try:
        filename = filedialog.askopenfilename(filetypes=[("H5 Files", "*.h5")])
        loaded_model = tf.keras.models.load_model(filename)

        # Convert the model to TensorFlow Lite format with post-training quantization
        converter = tf.lite.TFLiteConverter.from_keras_model(loaded_model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        tflite_model = converter.convert()

        # Save the quantized model to a file
        tflite_filename = f"{user_model_name}.tflite"
        with open(tflite_filename, 'wb') as f:
            f.write(tflite_model)

        file_size = os.path.getsize(tflite_filename)
        size_in_mb = file_size / (1024 * 1024)
        load_cmodel_label.config(text=f"Converted h5 to tflite model \n "
                                      f"File Name: {tflite_filename} \n"
                                      f"File Size: {size_in_mb:.2f}mb")

        cmodel = tflite_filename
    except Exception as e:
        display_error(f"Unable to load h5 model for conversion {e} \n try choosing a model form the file")


def load_tflite_model():
    global x, y
    input_shape = x.shape
    output_shape = y.shape
    print(input_shape)
    print(output_shape)
    try:
        interpreter = tf.lite.Interpreter(model_path=cmodel)
        interpreter.allocate_tensors()
        # Get input and output details
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        interpreter.resize_tensor_input(input_details[0]['index'], input_shape)
        interpreter.resize_tensor_input(output_details[0]['index'], output_shape)
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        x_test = np.array(x, dtype=np.float32)
        interpreter.set_tensor(input_details[0]['index'], x_test)
        interpreter.invoke()
        start_time = time.time()
        tflite_model_predictions = interpreter.get_tensor(output_details[0]['index'])
        print("prediction shape:", tflite_model_predictions.shape)
        prediction_classes = np.argmax(tflite_model_predictions, axis=1)
        end_time = time.time()
        true_labels = np.argmax(y, axis=1)

        acc = accuracy_score(prediction_classes, true_labels)
        execution_time = end_time - start_time
        load_lite_model_label.config(
            text=f"Model Evaluation:\nModel Accuracy: {acc * 100:.2f}% \n Execution Time: {execution_time:.2f} sec"
        )
    except Exception as e:
        display_error(f"An error occurred {e}")

    # single_action_eval_results_tf()


def submit_text():
    global user_model_name
    user_model_name = entry.get()


# GUI Setup

root = tk.Tk()
root.geometry("1500x700")
root.resizable(False, False)
# root.iconbitmap(default="ml.ico")
# root.tk.call('source', 'breeze.tcl')
# root['background'] = "#a7c8f2"


root.title("Train EMG Data")

# Dropdown Menu button and display table of contents
click_action = StringVar()
click_action.set("Only EMG1")
click_action.trace("w", on_select_option)

Action_menu = OptionMenu(root, click_action, "Only EMG1", "Only EMG2", "Only EMG3", "Only EMG1 and EMG2")
Action_menu.place(x=30, y=250)
Action_menu.config(width=22, height=2)

sensor_info_label = Frame(root, bg='white', width=200, height=100)
sensor_info_label.place(x=30, y=300)

sensor_info_label = Label(sensor_info_label, text="Shape info", font=("Arial", 9, "bold"))
sensor_info_label.pack()
# single action evaluation label for h5 model
single_action_evaluation = Label(root, text="Single Action Evaluation: ", wraplength=300, font=("Arial", 8, "bold"))
single_action_evaluation.place(x=1200, y=10)

# *******************************************************************************

# single action evaluation label for tflite model
single_action_evaluation_tf = Label(root, text="Single Action Evaluation Tflite: ", wraplength=200,
                                    font=("Arial", 8, "bold"))
single_action_evaluation_tf.place(x=1200, y=200)

# *******************************************************************************


frm1 = Frame(root, bg='black', width=2, height=650)
frm1.place(x=800, y=20)

frm2 = Frame(root, bg='black', width=2, height=650)
frm2.place(x=280, y=20)

frm3 = Frame(root, bg='grey', width=500, height=500)
frm3.place(x=290, y=100)

# textbox
# Create a label to describe the text box
label = tk.Label(root, text="Enter model name:")
label.place(x=30,y=440)

# Create the text box (Entry widget)
entry = tk.Entry(root)
entry.place(x=30, y=470)

# Create a submit button to get the entered text
submit_button = tk.Button(root, text="Submit", command=submit_text)
submit_button.place(x=30, y=500)

# import Data button and table data
Import_button = Button(root, text="Import Data", height=2, width=12, command=import_data)
Import_button.place(x=30, y=20)

# Label Information Section
label_info_frame = Frame(root, bg='white', width=200, height=100)
label_info_frame.place(x=30, y=80)

label_info_label = Label(label_info_frame, text="Shape info", font=("Arial", 9, "bold"))
label_info_label.pack()
# ******************************************************************************************

# load label
load_model_label = Label(root, text="Model: ", wraplength=150, font=("Arial", 9, "bold"))
load_model_label.place(x=820, y=90)

# evaluate label
evaluate_model_label = Label(root, text="Model Evaluation: ", wraplength=200, font=("Arial", 9, "bold"))
evaluate_model_label.place(x=1050, y=90)

# cmodel label to display info
load_cmodel_label = Label(root, text="Converted Model: \n", wraplength=200, font=("Arial", 9, "bold"))
load_cmodel_label.place(x=820, y=250)

# tflite model label to display evaluation
load_lite_model_label = Label(root, text="Evaluated Model", wraplength=150, font=("Arial", 9, "bold"))
load_lite_model_label.place(x=1050, y=250)

#  **********************************************************************************

Import_button = Button(root, text="Import Data", height=2, width=12, command=import_data)
Import_button.place(x=30, y=20)

Train_button = Button(root, text="Train Data", height=2, width=60, command=train_data)
Train_button.place(x=290, y=20)

Load_button = Button(root, text="Load Model", height=2, width=12, command=import_model)
Load_button.place(x=810, y=20)

Load_cmodel_button = Button(root, text="Import model [tflite conv]", height=2, width=12, command=load_cmodel,
                            wraplength=100)
Load_cmodel_button.place(x=820, y=200)

# load tflite model
Load_tflite_button = Button(root, text="Load TFLite Model", height=2, width=12, command=load_tflite_model,
                            wraplength=80)
Load_tflite_button.place(x=1050, y=200)

Eval_button = Button(root, text="Evaluate Model", height=2, width=12, command=evaluate_model)
Eval_button.place(x=1050, y=20)

Close_button = Button(root, text="Close", height=4, width=18, command=root.destroy)
Close_button.place(x=30, y=600)

root.mainloop()
