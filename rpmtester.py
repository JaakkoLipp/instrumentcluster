import RPi.GPIO as GPIO
import time
from time import sleep


def getrpm(RPM_PIN):
    # Set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RPM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    # Initialize variables
    falling_edges = 0
    prev_time = None
    frequencies = []
    num_samples = 2
    print("initialized")

    try:
        for x in range(num_samples):
            print("waiting for first edge")
            # Wait for the first falling edge
            edgeDetected = GPIO.wait_for_edge(RPM_PIN, GPIO.RISING, timeout=6000)
            if edgeDetected == None:  # If timeout occures, returns rpm 0. Times out if rpm is lower than 500
                rpm = 0
                GPIO.cleanup()
                print("timeout and exit")
                return rpm 
            
            # Measure time between falling edges
            if prev_time is not None:
                print("first pulse gotten")
                current_time = time.time()
                time_difference = current_time - prev_time
                frequency = 1.0 / time_difference  # Calculate frequency
                frequencies.append(frequency)
                falling_edges += 1
                
                
                # Exit after a specified number of samples
                if falling_edges >= num_samples:
                    print("all pulses gotten")
                    final_frequency = sum(frequencies) / len(frequencies)
                    rpm = final_frequency * 30  # Converting frequency to rpm (6000rpm = 200hz and 30rpm = 1hz)
            prev_time = time.time()
    except Exception: 
        pass
    GPIO.cleanup()
    print("returning calculated rpm")
    return rpm

while True:
    print(getrpm(27))
    sleep(5)
