from subprograms import *
from datetime import datetime
import time, os #spi #TODO: spi interface and imports
import RPi.GPIO as GPIO
#from machine import I2C

#TODO check if imports needed in subprograms

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

#TODO gpio input pins plox check correct
SPEEDPIN = 36 #speedometer input gpio pin
RPM_PIN= 37 #rpm input pin
QS_PIN = 23 #gpio output pin for quicshifter controlling, currently 1 for activated and 0 for disabled
NEUTRAL_LIST = ["/dev/spidev1.0", 5] #neutralpin adc [device, channel 0-7]
V12_READ_INPUTLIST = ["/dev/spidev1.0", 7] #12v sensing inputpin adc [device, channel 0-7]
WATERTEMP_INPUT_LIST = ["/dev/spidev1.1", 0, 5] #watertemp inputpin adc [device, channel 0-7], watertemp multiplier by resistance
RESERVEFUEL_INPUT_LIST = ["/dev/spidev1.1", 2, 5] #reservefuel inputpin adc [device, channel 0-7], reserve fuel state multiplier by resistance
BLINKER_LEFT_LIST = ["/dev/spidev1.0", 0]
BLINKER_RIGHT_LIST = ["/dev/spidev1.0", 1]
HI_BEAM_LIST = ["/dev/spidev1.0", 2]
LEFT_BUTTON_LIST = ["/dev/spidev1.0", 3]
RIGHT_BUTTON_LIST = ["/dev/spidev1.0", 4]
ENGINE_LIGHT_LIST = ["/dev/spidev1.0", 6]
OIL_LIGHT_LIST = ["/dev/spidev1.1", 3]
AMBIENT_LIGHT_LIST = ["/dev/spidev1.1", 1, 5] #ambientlight resistor inputpin adc [device, channel 0-7], ambient light multiplier by resistance
AMBIENT_TEMP_LIST = ["/dev/spidev1.1", 4, 5]  #ambient temperature resistor inputpin adc [device, channel 0-7], ambient temp multiplier by resistance


odo = odoread() #datatype kilometers
trip = tripread() #datatype kilometers
gear_speed_rpm = get_gear_speed_and_rpm()
odotime = time.time()
otherdata = otherdataread()
scene = 1 #which scene is first to start on poweron
tripcounter = 0.0
qs_status = 1 # set qs status as activated on startup
GPIO.setwarnings(False) # Sets any warnings off #TODO check if needed to fix


while True: 
    status = get_status()
    scene = sceneshifter(status, scene)
    scenereturn = scenedrawer(scene, status, odo, trip, qs_status)
    sceneout = scenereturn[0] #output string is 1. datapoint in list
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

    otherdata = otherdataread() #read otherdata [nightmode(1/0), reservefuelstate(1/0), watertemperature(str))
    
    gear_speed_rpm = get_gear_speed_and_rpm()  # update only gear, speed and rpm data to save process time
    ododata = send_data_and_calc_odo(odotime, gear_speed_rpm, status, sceneout, otherdata) #output data as printing and returning and calculating trip distance 
    odotime = ododata[1]
    odo = odo + ododata[0]
    trip = trip + ododata[0]

    if read_volts_12() < 8.0: #checking if power input is below voltagelimit of 8v. If true, shuts instrumentcluster down.
        time.sleep(1)
        if read_volts_12() <8.0: # Checking again that power is cutted to commit shutdown
            shutdownwrite(odo, trip)    # input shutdown commands here
            time.sleep(1)
            os.system("shutdown now -h") # Shutdown OPi. Power cutout after 15seconds
    else:
        time.sleep(0.01) #whileloop speed limiter
