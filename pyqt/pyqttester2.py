import sys
import random
import threading
import time
from time import sleep
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

# Function to update the text of the QLabel for rpmdata
def update_rpm():
    global rpmdata
    while True:
        rpmdata = random.randint(0, 8000)
        rpm_label.setText(f"RPM: {rpmdata}")
        time.sleep(0.03)  # Update more frequently

# Function to update the text of the QLabel for outputlist
def update_text():
    global outputlist
    while True:
        geardata = random.choice(gearoptions)
        speedata = random.randint(0, 200)
        enginelight = random.choice(options)
        oillight = random.choice(options)
        scene = "Data from main here :)"
        clocktime = time.strftime("%H:%M:%S", time.localtime())
        nightmode = random.choice(options)
        reservefuelstate = random.choice(options)
        watertemp = "92c"
        outputlist = [geardata, speedata, enginelight, oillight, scene, clocktime, nightmode, reservefuelstate, watertemp]
        update_gui()
        sleep(random.uniform(0, 1.5))  # Update every 2 seconds

# Function to update the GUI with the latest data
def update_gui():
    rpm_label.setText(f"RPM: {rpmdata}")
    for label, data in zip(labels, outputlist):
        label.setText(str(data))
        

# Create the Qt Application
app = QApplication(sys.argv)

# Create a QWidget to hold the layout
widget = QWidget()

# Create a QVBoxLayout to organize widgets vertically
layout = QVBoxLayout(widget)

# Create QLabel widgets to display data
rpm_label = QLabel()
layout.addWidget(rpm_label)

labels = [QLabel() for _ in range(9)]
for label in labels:
    layout.addWidget(label)

# Show the widget
widget.show()

# List of options
options = [True, False]
gearoptions = ["1", "N", "2", "3", "4", "5", "6"]

# Global variables for data
outputlist = []
rpmdata = 0

# Start a new thread to continuously update the outputlist
output_thread = threading.Thread(target=update_text)
output_thread.daemon = True
output_thread.start()

# Start a new thread to continuously update the rpmdata
rpm_thread = threading.Thread(target=update_rpm)
rpm_thread.daemon = True
rpm_thread.start()

# Start the Qt event loop
sys.exit(app.exec())
