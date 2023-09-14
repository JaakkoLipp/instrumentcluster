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


    while True: 
        get arvot
        print(kaikki arvot) 
        get arvotspeed,rpm, gear
        print(kaikki arvot) 
        get arvotspeed,rpm, gear
        print(kaikki arvot)

 