from subprograms import *
from datetime import datetime
import time, os #spi #TODO: spi interface and imports
import OPi.GPIO as GPIO
#from machine import I2C
from multiprocessing import Process
#TODO check if imports needed in subprograms


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
