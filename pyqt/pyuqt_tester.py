import sys
import random
import threading
import time
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

class RoundProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 100)
        self.setMaximumSize(100, 100)
        self.value = 0

    def setValue(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("#007bff"))
        pen.setWidth(8)
        painter.setPen(pen)

        painter.drawArc(10, 10, 80, 80, 30 * 16, (360 - 60) * 16)
        span = int((360 - 60) * (self.value / 10000)) * 16
        painter.drawArc(10, 10, 80, 80, 30 * 16, span)

# Function to update the text of the QLabel for rpmdata
def update_rpm():
    global rpmdata
    while True:
        rpmdata = random.randint(0, 10000)
        rpm_label.setText(f"RPM: {rpmdata}")
        rpm_progress.setValue(rpmdata)
        time.sleep(0.1)  # Update more frequently

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

# Function to update the GUI with the latest data
def update_gui():
    speed_label.setText(f"Speed: {outputlist[1]}")  # Update speed label
    for label, data in zip(labels, outputlist[2:]):
        label.setText(str(data))
    highbeam_label.setText(f"High Beam: {highbeam_state}")

# Create the Qt Application
app = QApplication(sys.argv)

# Create a QWidget to hold the layout
widget = QWidget()
widget.setAutoFillBackground(True)
palette = widget.palette()
palette.setColor(widget.backgroundRole(), QColor(240, 240, 240))  # Light gray background color
widget.setPalette(palette)

# Create a QVBoxLayout to organize widgets vertically
layout = QVBoxLayout(widget)

# QLabel for Speed
speed_label = QLabel()
speed_label.setFont(QFont("Arial", 20, QFont.Bold))  # Larger font size and bold
speed_label.setAlignment(Qt.AlignCenter)  # Align center
layout.addWidget(speed_label)

# Create QLabel widgets to display data
rpm_label = QLabel()
rpm_label.setFont(QFont("Arial", 14))  # Increase font size
rpm_label.setStyleSheet("background-color: white;")  # Set background color
layout.addWidget(rpm_label)

labels = [QLabel() for _ in range(8)]  # Reduced to 8 for better alignment
for label in labels:
    label.setFont(QFont("Arial", 12))  # Increase font size
    label.setStyleSheet("background-color: white;")  # Set background color
    layout.addWidget(label)

# QLabel for High Beam
highbeam_label = QLabel()
highbeam_label.setFont(QFont("Arial", 14))  # Increase font size
highbeam_label.setStyleSheet("background-color: white;")  # Set background color
layout.addWidget(highbeam_label)

# Progress bar for RPM meter
rpm_progress = RoundProgressBar()
layout.addWidget(rpm_progress)

# Show the widget
widget.show()

# List of options
options = ["On", "Off"]
gearoptions = ["Reverse", "Neutral", "First", "Second", "Third", "Fourth", "Fifth"]

# Global variables for data
outputlist = []
rpmdata = 0
highbeam_state = 'low'

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
highbeam_thread.daemon = True
highbeam_thread.start()

# Start the Qt event loop
sys.exit(app.exec())
