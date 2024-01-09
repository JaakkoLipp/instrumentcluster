from subprograms import *
import time, os
import RPi.GPIO as GPIO
import math
from datetime import datetime
import requests # For frontend data transfer
import spidev
import subprocess


# Global values for code::

CORRECTION = 1                                          # Speedometer CORRECTION value, 1,0 is stock from factory
GEAR_RATIO = [2.533, 2.053, 1.737, 1.524, 1.381, 1.304] # Gear 1 to 6 ratios
GEAR_SENSITIVITY = 0.10                                 # How much variability allowed around calculated gear ratios to display calculated gear
SPEEDRATIO = 0.779221                                   # The ratio between speed and frequency (how many kmh per hz) for example( 60kmh / 77hz = 0.779221 kmh/hz)
FRONT_SPROCKET_PULSES_PER_ROTATION = 4                  # How many pulses speedsensor sends each rotation of front sprocket
MULTIPLIER_12V = 5.17                                   # Value to calculate voltage of ADC voltage divider output. Must be defined to run code correctly!!  #TODO check multiplier value
HIREADLIMIT = 500                                       # Adc output value which is minimum for activation of hiread, used for positive voltage input (+)
LOWREADLIMIT = 500                                      # Adc output value which is maximum for activation of lowread, used for ground sensing input (-)
NIGHTMODETHRESHOLD= 1000                                # ADC data for nightmode activation threshold (0-1023)
BUTTONSLEEP = 2                                         # Time in seconds to detect long press
SCENEMAX = 4                                            # How many changing scenes is available by scene change button

# Gpio pins in BCM::

SPEEDPIN = 17                                            # Speedometer input pin
RPM_PIN = 27                                            # Rpm input pin
BLINKER_LEFT_PIN = 13                                   # Left blinker input pin
BLINKER_RIGHT_PIN = 6                                   # Right blinker input pin
HI_BEAM_PIN = 22                                        # High beam input pin
ENGINE_LIGHT_PIN = 26                                   # Fi or engine light input pin
OIL_LIGHT_PIN = 19                                      # Oil pressure light input pin
AMBIENT_TEMP_PIN = 24                                   # 1 wire ambient temperature sensor, DS18B20, does not affect code, just for connection note  


#Mcp3008 pins from 0-7::

LEFT_BUTTON_LIST = 0                                    # ADC input pin for right button 12v [channel 0-7]
RIGHT_BUTTON_LIST = 1                                   # ADC input pin for left button 12v [channel 0-7]
AMBIENT_LIGHT_LIST = 2                                  # ADC input pin for ambiet light photoresistor, purple wire, resistor connects to 12v [channel 0-7]
V12_READ_INPUTLIST = 4                                  # ADC input pin for +12V [channel 0-7]
RESERVEFUEL_INPUT_LIST = 5                              # ADC input pin for fuel light sensor, connects to ground through sensor [channel 0-7]
NEUTRAL_LIGHT_LIST = 6                                  # ADC input pin for neutral light sensor, connects to ground through switch [channel 0-7]
WATERTEMP_INPUT_LIST = 7                                # ADC input pin for water temperature sensor, connects to ground through swnsor [channel 0-7]

#SPI pins can be found in subprograms.py, analog_read()

# Currently not in use::

QS_PIN = 29                                             # Gpio output pin for quickshifter controlling, 1 for activated and 0 for disabled
XX_PIN = 4                                              # 1.st channel in level converter, currently not connected
XX_LIST = 3                                             # Free ADC pin, positive 12v [channel 0-7]


#############  Main code  ##############

# Setting gpio mode
GPIO.setmode(GPIO.BCM)
GPIO_INPUT_LIST = [SPEEDPIN, RPM_PIN, BLINKER_LEFT_PIN, BLINKER_RIGHT_PIN, HI_BEAM_PIN, ENGINE_LIGHT_PIN, OIL_LIGHT_PIN, XX_PIN]
for pin in GPIO_INPUT_LIST:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


# Add an event detection for the pin (both rising and falling edges)
GPIO.add_event_detect(BLINKER_LEFT_PIN, GPIO.BOTH, callback=pin_changed_callback(BLINKER_LEFT_PIN))
GPIO.add_event_detect(BLINKER_RIGHT_PIN, GPIO.BOTH, callback=pin_changed_callback(BLINKER_RIGHT_PIN))
GPIO.add_event_detect(BLINKER_RIGHT_PIN, GPIO.BOTH, callback=pin_changed_callback(HI_BEAM_PIN))

odo = odoread()   # Datatype kilometers
trip = tripread() # Datatype kilometers
gear_speed_rpm = get_gear_speed_and_rpm(RPM_PIN, NEUTRAL_LIGHT_LIST, FRONT_SPROCKET_PULSES_PER_ROTATION, GEAR_RATIO, GEAR_SENSITIVITY, LOWREADLIMIT, SPEEDPIN, SPEEDRATIO, CORRECTION)
odotime = time.time()
otherdata = otherdataread(AMBIENT_LIGHT_LIST, NIGHTMODETHRESHOLD, WATERTEMP_INPUT_LIST, RESERVEFUEL_INPUT_LIST)
scene = 1 # Defines first scene to start on poweron
tripcounter = 0.0
qs_status = 1 # Sets qs status as activated on startup
GPIO.setwarnings(False) # Sets any Gpio warnings off
subprocess.Popen(['python3', 'rpmreader.py'])


while True: 
    status = get_status(LEFT_BUTTON_LIST, RIGHT_BUTTON_LIST, ENGINE_LIGHT_PIN, OIL_LIGHT_PIN, BUTTONSLEEP, HIREADLIMIT)
    scene = sceneshifter(status, scene, SCENEMAX)
    scenereturn = scenedrawer(scene, status, odo, trip, qs_status, QS_PIN, V12_READ_INPUTLIST, MULTIPLIER_12V)
    sceneout = scenereturn[0] # Output string is 1. datapoint in list, QS_PIN, V12_READ_INPUTLIST, MULTIPLIER_12V
    if scene == 2:
        trip = scenereturn[1] # If reset button have been used, scenereturn 2. datapoint is new trip(0.0)
    elif scene == 5:
        qs_status = scenereturn[1]
    
    gear_speed_rpm = get_gear_speed_and_rpm(RPM_PIN, NEUTRAL_LIGHT_LIST, FRONT_SPROCKET_PULSES_PER_ROTATION, GEAR_RATIO, GEAR_SENSITIVITY, LOWREADLIMIT, SPEEDPIN, SPEEDRATIO, CORRECTION)  # Updates only gear, speed and rpm data to save process time
    ododata = send_data_and_calc_odo(odotime, gear_speed_rpm, status, sceneout, otherdata) #output data as printing and returning and calculating trip distance
    odotime = ododata[1]       # 2.nd item of odotime list is time of last measure
    odo = odo + ododata[0]     # 1.st item of odotime list is distance between last two displayed speed 
    trip = trip + ododata[0]

    tripcounter = tripcounter + ododata[0] # After about every full kilometer from starting program, write odo and trip to txt file
    if tripcounter > 0.5:
        shutdownwrite(odo, trip)
        tripcounter = 0.0

    otherdata = otherdataread(AMBIENT_LIGHT_LIST, NIGHTMODETHRESHOLD, WATERTEMP_INPUT_LIST, RESERVEFUEL_INPUT_LIST) # Reads otherdata [nightmode(1/0), reservefuelstate(1/0), watertemperature(str))
    
    gear_speed_rpm = get_gear_speed_and_rpm(RPM_PIN, NEUTRAL_LIGHT_LIST, FRONT_SPROCKET_PULSES_PER_ROTATION, GEAR_RATIO, GEAR_SENSITIVITY, LOWREADLIMIT, SPEEDPIN, SPEEDRATIO, CORRECTION)  # Updates only gear, speed and rpm data to save process time
    ododata = send_data_and_calc_odo(odotime, gear_speed_rpm, status, sceneout, otherdata) # Outputs data as sending it to local server with requests and returns and calculates trip distance
    odotime = ododata[1]
    odo = odo + ododata[0]
    trip = trip + ododata[0]

    if read_volts_12(V12_READ_INPUTLIST, MULTIPLIER_12V) < 8.0: # Checks if power input is below voltagelimit of 8v. If true, shuts instrumentcluster down.
        time.sleep(1)
        if read_volts_12(V12_READ_INPUTLIST, MULTIPLIER_12V) <8.0: # Checks again if voltage is under 8 volts
            shutdownwrite(odo, trip)    # Commands needed to run before shutdown, saves odo and trip
            time.sleep(1)
            os.system("shutdown now -h") # Shuts down the system.
    
