import RPi.GPIO as GPIO
import time

# Set the GPIO mode to BCM
GPIO.setmode(GPIO.BCM)

# Set the GPIO pin number you want to use
gpio_pin = 17  # Change this to your actual GPIO pin number

# Setup the GPIO pin as an input with pull-down resistor enabled
GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

try:
    while True:
        for _ in range(10):
            # Read the state of the GPIO pin
            pin_state = GPIO.input(gpio_pin)

            # Print the pin state
            print(f"GPIO Pin {gpio_pin} state: {pin_state}")

            # Delay for 0.1 second (100 milliseconds)
            time.sleep(0.1)

except KeyboardInterrupt:
    print("Program terminated by user.")
finally:
    # Cleanup GPIO settings on program exit
    GPIO.cleanup()