from subprograms import *
import time, os, math, sys #spi #TODO: spi interface and imports
#import OPi.GPIO as GPIO
#from machine import I2C
from multiprocessing import Process
#TODO check if imports needed in subprograms

from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def indexpage():
    return render_template('index.html')

if __name__ == '__main__':
    #TODO app.run()

    odo = odoread()
    trip = tripread()
    gear_speed_rpm = get_gear_speed_and_rpm()
    odotime = time.time()
    otherdata = otherdataread()
    scene = 1


    while True: 
        status = getstatus()
        scenereturn = scenedrawer(scene, status, odo, trip)
        sceneout = scenereturn[0] #output string is 1. datapoint in list
        if scene == 2:
            trip = scenereturn[1] #if reset button have been used, scenereturn 2. datapoint is new trip(0.0)
		
        ododata = printdata_and_calc_odo(odotime, gear_speed_rpm, status, sceneout, otherdata) 
	odotime = ododata[1]
	odo = odo + ododata[0]
	trip = trip + ododata[0]

	otherdata = otherdataread()
	    
        gear_speed_rpm = get_gear_speed_and_rpm()  # update only gear, speed and rpm data to save process time
        ododata = printdata_and_calc_odo(odotime, gear_speed_rpm, status, sceneout, otherdata) 
	odotime = ododata[1]
	odo = odo + ododata[0]
	trip = trip + ododata[0] 
    
        if read_volts_12() < 8.0: #checking if power input is below voltagelimit of 8v. If true, shuts instrumentcluster down.
	        time.sleep(2)
            if read_volts_12() <8.0: # Checking again that power is cutted to commit shutdown
                def shutdownwrite(odo, trip)
                # input shutdown commands here
                time.sleep(3)
                os.system("shutdown now -h")
        else:
            time.sleep(0.05)
        

 
