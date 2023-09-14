import subprograms
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
    app.run()

    """
    Backend here
    @elias

    """
