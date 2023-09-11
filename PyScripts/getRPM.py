import RPi.GPIO as GPIO
import time

def getrpm(gpio_pin):
    # Set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Initialize variables
    prev_time = None
    frequencies = []
    num_samples = 10

    try:
        for x in range(num_samples):
            # Wait for the first falling edge
            GPIO.wait_for_edge(gpio_pin, GPIO.FALLING)
            
            # Measure time between falling edges
            if prev_time is not None:
                current_time = time.time()
                time_difference = current_time - prev_time
                frequency = 1.0 / time_difference  # Calculate frequency
                frequencies.append(frequency)
                
            prev_time = time.time()
        # frequency to rpm and average as final_frequency
        final_frequency = sum(frequencies) / len(frequencies)
        rpm = final_frequency * 30  # Converting frequency to rpm (6000rpm = 200hz and 30rpm = 1hz)

    except KeyboardInterrupt:
        pass
    
    finally:
        GPIO.cleanup()
        return rpm
