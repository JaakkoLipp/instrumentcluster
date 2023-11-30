from subprograms import *
import time, os #spi #TODO: spi interface and imports
import RPi.GPIO as GPIO
import math
from datetime import datetime
import requests # For frontend data transfer
import spidev

CORRECTION = 1 #speedometer CORRECTION value, 1,0 is stock from factory
GEAR_RATIO = [2.533, 2.053, 1.737, 1.524, 1.381, 1.304] # gears 1 to 6 ratios
GEAR_SENSITIVITY = 0.10 # How much variability allowed around calculated gear ratios
SPEEDRATIO = 0.779221 # ratio between speed and frequency (how many kmh per hz) for example( 60kmh / 77hz = 0.779221 kmh/hz)
FRONT_SPROCKET_PULSES_PER_ROTATION = 4 # How many pulses speedsensor sends each rotation of front sprocket
MULTIPLIER_12V = 1 # Must be defined to run code correctly!!  #TODO check multiplier value
HIREADLIMIT = 0.6 #adc output value which is minimum for activation of hiread, used for positive voltage input
LOWREADLIMIT = 0.25 #adc output value which is maximum for activation of lowread, used for ground sensing input
NIGHTMODETHRESHOLD= 30 #TODO #resistance for nightmode activation threshold
BUTTONSLEEP = 0.8 #sleeptime to detect long press
SCENEMAX = 4 #How many changing scenes is available by scene change button

# gpio pins:

SPEEDPIN = 29 #speedometer input gpio pin
RPM_PIN= 31 #rpm input pin
QS_PIN = 33 #gpio output pin for quicshifter controlling, currently 1 for activated and 0 for disabled

BLINKER_LEFT_PIN = 11
BLINKER_RIGHT_PIN = 13
HI_BEAM_PIN = 15
ENGINE_LIGHT_PIN = 16
OIL_LIGHT_PIN = 18


#TODO gpio input pins plox check correct

#mcp3008 pins from 0-7

V12_READ_INPUTLIST = mcp3008.CH0 #12v sensing inputpin adc [channel 0-7]
WATERTEMP_INPUT_LIST = mcp3008.CH1 #watertemp inputpin adc [channel 0-7], watertemp multiplier by resistance, defined in subprogarams
RESERVEFUEL_INPUT_LIST = mcp3008.CH2 #reservefuel inputpin adc [channel 0-7], reserve fuel state multiplier by resistance
AMBIENT_LIGHT_LIST = mcp3008.CH3 #ambientlight resistor inputpin adc [channel 0-7], ambient light multiplier by resistance
AMBIENT_TEMP_LIST = mcp3008.CH4 #ambient temperature resistor inputpin adc [channel 0-7], ambient temp multiplier by resistance
LEFT_BUTTON_LIST = mcp3008.CH5
RIGHT_BUTTON_LIST = mcp3008.CH6
NEUTRAL_LIST = mcp3008.CH7 #neutralpin adc [device, channel 0-7]


odo = odoread() #datatype kilometers
trip = tripread() #datatype kilometers
gear_speed_rpm = get_gear_speed_and_rpm(RPM_PIN, NEUTRAL_LIST, FRONT_SPROCKET_PULSES_PER_ROTATION, GEAR_RATIO, GEAR_SENSITIVITY, LOWREADLIMIT, SPEEDPIN, SPEEDRATIO, CORRECTION)
odotime = time.time()
otherdata = otherdataread(AMBIENT_LIGHT_LIST, NIGHTMODETHRESHOLD, WATERTEMP_INPUT_LIST, RESERVEFUEL_INPUT_LIST)
scene = 1 #which scene is first to start on poweron
tripcounter = 0.0
qs_status = 1 # set qs status as activated on startup
GPIO.setwarnings(False) # Sets any warnings off #TODO check if needed to fix
spi = spidev.SpiDev()
spi.open(0, 0)

while True: 
    status = get_status(BLINKER_LEFT_LIST, BLINKER_RIGHT_LIST,HI_BEAM_LIST, LEFT_BUTTON_LIST, RIGHT_BUTTON_LIST, ENGINE_LIGHT_LIST, OIL_LIGHT_LIST, BUTTONSLEEP, HIREADLIMIT, LOWREADLIMIT)
    scene = sceneshifter(status, scene, SCENEMAX)
    scenereturn = scenedrawer(scene, status, odo, trip, qs_status, QS_PIN, V12_READ_INPUTLIST, MULTIPLIER_12V, AMBIENT_TEMP_LIST)
    sceneout = scenereturn[0] #output string is 1. datapoint in list, QS_PIN, V12_READ_INPUTLIST, MULTIPLIER_12V, AMBIENT_TEMP_LIST
    if scene == 2:
        trip = scenereturn[1] #if reset button have been used, scenereturn 2. datapoint is new trip(0.0)
    elif scene == 5:
        qs_status = scenereturn[1]
    
    ododata = send_data_and_calc_odo(odotime, gear_speed_rpm, status, sceneout, otherdata) #output data as printing and returning and calculating trip distance
    odotime = ododata[1] # 2.nd item of list is time of last measure
    odo = odo + ododata[0] # 1.st item of list is distance between last two displayed speed 
    trip = trip + ododata[0]

    tripcounter = tripcounter + ododata[0] # After about every full kilometer from starting program, write odo and trip to txt file
    if tripcounter > 0.5:
        shutdownwrite(odo, trip)
        tripcounter = 0.0

    otherdata = otherdataread(AMBIENT_LIGHT_LIST, NIGHTMODETHRESHOLD, WATERTEMP_INPUT_LIST, RESERVEFUEL_INPUT_LIST) #read otherdata [nightmode(1/0), reservefuelstate(1/0), watertemperature(str))
    
    gear_speed_rpm = get_gear_speed_and_rpm(RPM_PIN, NEUTRAL_LIST, FRONT_SPROCKET_PULSES_PER_ROTATION, GEAR_RATIO, GEAR_SENSITIVITY, LOWREADLIMIT, SPEEDPIN, SPEEDRATIO, CORRECTION)  # update only gear, speed and rpm data to save process time
    ododata = send_data_and_calc_odo(odotime, gear_speed_rpm, status, sceneout, otherdata) #output data as printing and returning and calculating trip distance 
    odotime = ododata[1]
    odo = odo + ododata[0]
    trip = trip + ododata[0]

    if read_volts_12(V12_READ_INPUTLIST, MULTIPLIER_12V) < 8.0: #checking if power input is below voltagelimit of 8v. If true, shuts instrumentcluster down.
        time.sleep(1)
        if read_volts_12(V12_READ_INPUTLIST, MULTIPLIER_12V) <8.0: # Checking again that power is cutted to commit shutdown
            shutdownwrite(odo, trip)    # input shutdown commands here
            time.sleep(1)
            os.system("shutdown now -h") # Shutdown OPi. Power cutout after 15seconds
    else:
        time.sleep(0.01) #whileloop speed limiter
