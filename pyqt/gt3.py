import sys
import random
import threading
import time
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

# Function to update the text of the QLabel for rpmdata
def update_rpm():
    global rpmdata
    while True:
        rpmdata = random.randint(0, 8000)
        rpm_label.setText(f"RPM: {rpmdata}")
        time.sleep(0.01)  # Update more frequently

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
        time.sleep(2)  # Update every 2 seconds

# Function to update the highbeam QLabel
def update_highbeam():
    global highbeam_state
    while True:
        highbeam_state = random.choice(['high', 'low'])
        highbeam_label.setText(f"High Beam: {highbeam_state}")
        time.sleep(1)  # Update every second

def update_blinkerleft():
    global blinkerleft_state
    while True:
        blinkerleft_state = random.choice(['high', 'low'])
        blinkerleft_label.setText(f"blönk lef: {blinkerleft_state}")
        time.sleep(1)  # Update every second

def update_blinkerright():
    global blinkerright_state
    while True:
        blinkerright_state = random.choice(['high', 'low'])
        blinkerright_label.setText(f"blink röch: {blinkerright_state}")
        time.sleep(1)  # Update every second

# Function to update the GUI with the latest data
def update_gui():
    rpm_label.setText(f"RPM: {rpmdata}")
    for label, data in zip(labels, outputlist):
        label.setText(str(data))
    highbeam_label.setText(f"High Beam: {highbeam_state}")
    blinkerleft_label.setText(f"left blonker: {blinkerleft_state}")
    blinkerright_label.setText(f"right one: {blinkerright_state}")

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

# QLabel for High Beam
highbeam_label = QLabel()
layout.addWidget(highbeam_label)

blinkerleft_label = QLabel()
layout.addWidget(blinkerleft_label)

blinkerright_label = QLabel()
layout.addWidget(blinkerright_label)

# Show the widget
widget.show()

# List of options
options = [True, False]
gearoptions = ["1", "N", "2", "3", "4", "5", "6"]


# Global variables for data
outputlist = []
rpmdata = 0
highbeam_state = False
blinkerleft_state = False
blinkerright_state = False


# Start a new thread to continuously update the outputlist
output_thread = threading.Thread(target=update_text)
output_thread.daemon = True
output_thread.start()

# Start a new thread to continuously update the rpmdata
rpm_thread = threading.Thread(target=update_rpm)
rpm_thread.daemon = True
rpm_thread.start()

# Start a new thread to continuously update the highbeam state
highbeam_thread = threading.Thread(target=update_highbeam)
blinkerleft_thread = threading.Thread(target=update_blinkerleft)
blinkerright_thread = threading.Thread(target=update_blinkerright)
highbeam_thread.daemon = True
highbeam_thread.start()
blinkerleft_thread.start()
blinkerright_thread.start()

# Start the Qt event loop
sys.exit(app.exec())
