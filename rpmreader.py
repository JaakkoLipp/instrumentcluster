import RPi.GPIO as GPIO
import time
import requests



def getrpm(RPM_PIN):

    GPIO.setup(RPM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    # Initialize variables
    falling_edges = 0
    prev_time = None
    frequencies = []
    num_samples = 3

    try:
        for x in range(num_samples):
            # Wait for the first falling edge
            edgeDetected = GPIO.wait_for_edge(RPM_PIN, GPIO.RISING, timeout=60)
            if edgeDetected == None:  # If timeout occures, returns rpm 0. Times out if rpm is lower than 500
                return 0 
            
            # Measure time between falling edges
            if prev_time is not None:
                current_time = time.time()
                time_difference = current_time - prev_time
                frequency = 1.0 / time_difference  # Calculate frequency
                if frequency < 500:
                    frequencies.append(frequency)
                falling_edges += 1
                
                
                # Exit after a specified number of samples
                if falling_edges >= num_samples-1:
                    rpm = (sum(frequencies) / len(frequencies)) * 30  # Converting frequency to rpm (6000rpm = 200hz and 30rpm = 1hz)
            prev_time = time.time()
    except Exception: 
        pass
    return rpm

###############  Code  ###############

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False) # Sets any Gpio warnings off
RPM_PIN = 23 

while True:
  rpm = round(getrpm(RPM_PIN), 0)

#TODO: Datasend jaakko

  sleep(0.01)
