import random
from time import sleep
from datetime import datetime
import sys
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget

options = [True, False]
gearoptions = ["1", "N", "2", "3", "4"]


# Function to change the text of the QLabel
def change_text():
    label.setText('New Text')

# Create the Qt Application
app = QApplication(sys.argv)

# Create a QWidget to hold the layout
widget = QWidget()

# Create a QVBoxLayout to organize widgets vertically
layout = QVBoxLayout(widget)

# Create a QLabel widget (a simple text label)
label = QLabel('Hello, PySide!')

# Create a QPushButton to change the text
button = QPushButton('Change Text')
button.clicked.connect(change_text)

# Add the label and button to the layout
layout.addWidget(label)
layout.addWidget(button)

# Show the widget
widget.show()

# Start the Qt event loop
sys.exit(app.exec())

while True:
    geardata = random.choice(gearoptions)
    speedata = random.randint(0, 200)
    enginelight = random.choice(options)
    oillight = random.choice(options)
    scene = "Data from main here :)"
    clocktime = datetime.now().strftime("%H:%M:%S")
    nightmode = random.choice(options)
    reservefuelstate = random.choice(options)
    watertemp = "92c"
    outputlist = [geardata, speedata, enginelight, oillight, scene, clocktime, nightmode, reservefuelstate, watertemp]
    print(outputlist)
    sleep(2)
