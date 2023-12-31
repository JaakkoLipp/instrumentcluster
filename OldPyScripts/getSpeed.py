import RPi.GPIO as GPIO
import time

def getspeed(gpio_pin, correction):
    # Set up GPIO
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Initialize variables
    falling_edges = 0
    prev_time = None
    frequencies = []
    num_samples = 1
    sampler = 0

    if correction == None:
        correction = 1.0
    try:
        #Do-While loop in python
        while True:
            # Wait for the first falling edge
            GPIO.wait_for_edge(gpio_pin, GPIO.FALLING)
            
            # Measure time between falling edges
            if prev_time is not None:
                current_time = time.time()
                time_difference = current_time - prev_time
                frequency = 1.0 / time_difference  # Calculate frequency
                frequencies.append(frequency)
                falling_edges += 1
                if sampler == 0:   # Going to run only once to determinate sample size
                    if frequency <=4:
                        num_samples = 1
                    if frequency > 4 and frequency < 8:
                        num_samples = 2
                    if frequency >= 8 and frequency < 15:
                        num_samples = 4
                    if frequency >= 15 and frequency < 40:
                        num_samples = 7
                    else:
                        num_samples = 12
                sampler = 1     # Rising sampler not to run sampler loop again
                
                # Exit after a specified number of samples
                if falling_edges >= num_samples:
                    final_frequency = sum(frequencies) / len(frequencies)
                    speed = final_frequency * 0.779221  # Converting frequency to kmh ( 60kmh = 77hz)
                    corrected_speed = speed * correction # Correcting speed for known measuring error
                    break
                elif len(frequencies) > 50:
                    # this causes immense pain + auygh
                    break
            
            prev_time = time.time()
    
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        return corrected_speed
