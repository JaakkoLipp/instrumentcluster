import time, os, math, sys #spi #TODO: spi interface and imports
#import OPi.GPIO as GPIO
#from machine import I2C
from multiprocessing import Process

CORRECTION = 1 #speedometer CORRECTION value, 1,0 is stock from factory
GEAR_RATIO = [2.533, 2.053, 1.737, 1.524, 1.381, 1.304] # gears 1 to 6 ratios
GEAR_SENSITIVITY = 0.10 # How much variability allowed around calculated gear ratios
SPEEDRATIO = 0.779221 # ratio between speed and frequency (how many kmh per hz) for example( 60kmh / 77hz = 0.779221 kmh/hz)
FRONT_SPROCKET_PULSES_PER_ROTATION = 4 # How many pulses speedsensor sends each rotation of front sprocket
MULTIPLIER_12V = 1 # Must be defined to run code correctly!!  #TODO check multiplier value
HIREADLIMIT = 0.6
LOWREADLIMIT = 0.25

#TODO gpio input pins plox check correct
SPEEDPIN = 1 #speedometer input gpio pin
RPM_PIN = 2 #rpm input pin
NEUTRAL_LIST = ["/dev/spidev1.0", 5] #neutralpin adc [device, channel 0-7]
V12_READ_INPUTLIST = ["/dev/spidev1.0", 7] #12v sensing inputpin adc [device, channel 0-7]
WATERTEMP_INPUT_LIST = ["/dev/spidev1.1", 0, 5] #watertemp inputpin adc [device, channel 0-7], watertemp multiplier by resistance
RESERVEFUEL_INPUT_LIST = [["/dev/spidev1.1", 2, 5]] #reservefuel inputpin adc [device, channel 0-7], reserve fuel state multiplier by resistance
BLINKER_LEFT_LIST = ["/dev/spidev1.0", 0]
BLINKER_RIGHT_LIST = ["/dev/spidev1.0", 1]
HI_BEAM_LIST = ["/dev/spidev1.0", 2]
LEFT_BUTTON_LIST = ["/dev/spidev1.0", 3]
RIGHT_BUTTON_LIST = ["/dev/spidev1.0", 4]
ENGINE_LIGHT_LIST = ["/dev/spidev1.0", 6]
OIL_LIGHT_LIST = ["/dev/spidev1.1", 3]
AMBIENT_LIGHT_LIST = ["/dev/spidev1.1", 1, 5] #ambientlight resistor inputpin adc [device, channel 0-7], ambient light multiplier by resistance
AMBIENT_TEMP_LIST = ["/dev/spidev1.1", 4, 5]  #ambient temperature resistor inputpin adc [device, channel 0-7], ambient temp multiplier by resistance

def read_volts_12(): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    device = V12_READ_INPUTLIST[0]
    channel = V12_READ_INPUTLIST[1]
    status = spi.openSPI(device, speed=1000000)
    adc = spi.transfer((1,(8+channel)<<4,0))
    data = ((adc[1]&3) << 8) + adc[2]
    spi.close()
    finaldata = (data / 1023) * (3.3 * MULTIPLIER_12V)
    return finaldata


def read_hi(devicechannellist): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    device = devicechannellist[0]
    channel = devicechannellist[1]
    status = spi.openSPI(device, speed=1000000)
    adc = spi.transfer((1,(8+channel)<<4,0))
    data = ((adc[1]&3) << 8) + adc[2]
    spi.close()
    if data > HIREADLIMIT:
        finaldata = 1
    else:
        finaldata = 0
    return finaldata


def read_low(devicechannellist): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    device = devicechannellist[0]
    channel = devicechannellist[1]
    status = spi.openSPI(device, speed=1000000)
    adc = spi.transfer((1,(8+channel)<<4,0))
    data = ((adc[1]&3) << 8) + adc[2]
    spi.close()
    if data < LOWREADLIMIT:
        finaldata = 1
    else:
        finaldata = 0
    return finaldata

def read_ambient_light(): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    device = AMBIENT_LIGHT_LIST[0]
    channel = AMBIENT_LIGHT_LIST[1]
    multiplier = AMBIENT_LIGHT_LIST[2]
    status = spi.openSPI(device, speed=1000000)
    adc = spi.transfer((1,(8+channel)<<4,0))
    data = ((adc[1]&3) << 8) + adc[2]
    spi.close()
    resistance = (data / 1023) * (3.3 * multiplier)
    light_level = resistance #TODO check light level resistance curve to use!!!
    return light_level

def read_ambient_temperature(): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    device = AMBIENT_TEMP_LIST[0]
    channel = AMBIENT_TEMP_LIST[1]
    multiplier = AMBIENT_TEMP_LIST[2]
    status = spi.openSPI(device, speed=1000000)
    adc = spi.transfer((1,(8+channel)<<4,0))
    data = ((adc[1]&3) << 8) + adc[2]
    spi.close()
    resistance = (data / 1023) * (3.3 * multiplier)
    temperature = resistance #TODO check ambient temperature probe resistance curve to use!!!
    return temperature


def read_watertemperature(): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    device = WATERTEMP_INPUT_LIST[0]
    channel = WATERTEMP_INPUT_LIST[1]
    multiplier = WATERTEMP_INPUT_LIST[2]
    status = spi.openSPI(device, speed=1000000)
    adc = spi.transfer((1,(8+channel)<<4,0))
    data = ((adc[1]&3) << 8) + adc[2]
    spi.close()
    resistance = (data / 1023) * (3.3 * multiplier)
    temperature = -30.57 * math.log(resistance) + 212.11
    return temperature


def read_reservefuelstate(): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    device = RESERVEFUEL_INPUT_LIST[0]
    channel = RESERVEFUEL_INPUT_LIST[1]
    multiplier = RESERVEFUEL_INPUT_LIST[2]
    status = spi.openSPI(device, speed=1000000)
    adc = spi.transfer((1,(8+channel)<<4,0))
    data = ((adc[1]&3) << 8) + adc[2]
    spi.close()
    resistance = (data / 1023) * (3.3 * multiplier)
    if resistance < 22:
        reservefuel = 1
    else:
        reservefuel = 0
    return reservefuel


def getspeed():
    # Set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SPEEDPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Initialize variables
    falling_edges = 0
    prev_time = None
    frequencies = []
    num_samples = 1
    sampler = 0

    if CORRECTION == None:
        CORRECTION = 1.0
    try:
        while True:
            # Wait for the first falling edge
            
            
            if GPIO.wait_for_edge(SPEEDPIN, GPIO.FALLING, timeout=260) is None:  #if timeout occures, return speed 0
                return [0, 0] 
            # Measure time between falling edges
            if prev_time is not None:
                time_difference = time.time() - prev_time
                frequency = 1.0 / time_difference  # Calculate frequency
                frequencies.append(frequency)
                falling_edges += 1
                if sampler == 0:   # Going to run only once to determinate sample size
                    if frequency <=4: #at low speeds using smaller sample size for shorter sampling times
                        num_samples = 1
                    if frequency > 4 and frequency < 8:
                        num_samples = 2
                    if frequency >= 8 and frequency < 15:
                        num_samples = 3
                    if frequency >= 15 and frequency < 40:
                        num_samples = 4
                    else:
                        num_samples = 5
                sampler = 1     # Rising sampler not to run sampler loop again
                
                # Exit after a specified number of samples
                if falling_edges >= num_samples:
                    final_frequency = sum(frequencies) / len(frequencies)
                    speed = final_frequency * SPEEDRATIO  # Converting frequency to kmh using speed ratio
                    corrected_speed = speed * CORRECTION # Correcting speed for known measuring error
                    break
            
            prev_time = time.time()
    
    except KeyboardInterrupt:
        pass
    
    finally:
        GPIO.cleanup()
        return [corrected_speed, final_frequency]
    

def getrpm(SPEEDPIN):
    # Set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SPEEDPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Initialize variables
    falling_edges = 0
    prev_time = None
    frequencies = []
    num_samples = 4

    try:
        for x in range(num_samples):
            # Wait for the first falling edge
            GPIO.wait_for_edge(SPEEDPIN, GPIO.FALLING)
            
            # Measure time between falling edges
            if prev_time is not None:
                current_time = time.time()
                time_difference = current_time - prev_time
                frequency = 1.0 / time_difference  # Calculate frequency
                frequencies.append(frequency)
                falling_edges += 1
                
                
                # Exit after a specified number of samples
                if falling_edges >= num_samples:
                    final_frequency = sum(frequencies) / len(frequencies)
                    rpm = final_frequency * 30  # Converting frequency to rpm (6000rpm = 200hz and 30rpm = 1hz)
            prev_time = time.time()
    except Exception: 
        pass
    GPIO.cleanup()
    return rpm
    
    

def get_gear_speed_and_rpm(): #returns list containing [str:gear, int:speed km/h, int:rpm]
    
    getspeed = getspeed(SPEEDPIN, CORRECTION, SPEEDRATIO)  #gets speed and speed signal frequency
    speed = getspeed[0]
    speed_frequency = getspeed[1]

    rpm = getrpm(RPM_PIN)   #gets rpm

    if (read_low(NEUTRAL_LIST) == 1): #reads if neutral pin low or not. If low N is displayed.
        return (["N", speed, rpm])
    else:

        front_sprocket_speed = (speed_frequency / FRONT_SPROCKET_PULSES_PER_ROTATION) * 60 # Change revolutions per second to rpm 
        clutch_rpm = rpm / 1.611 # clutch / crank reduction ratio
        ratio = clutch_rpm / front_sprocket_speed
        for i in range(6):
            if (abs(ratio-GEAR_RATIO[i]) < GEAR_SENSITIVITY):
                return ([str(i + 1), speed, rpm])
        return (["-", speed, rpm])
    

def get_status():  # status output 7 segment list: [blinker left, blinker right, hi beam, left button, right button, engine light, oil light]. when on, state is 1, when off state is 0
    blinker_left = read_hi(BLINKER_LEFT_LIST)
    blinker_right = read_hi(BLINKER_RIGHT_LIST)
    hi_beam = read_hi(HI_BEAM_LIST)
    left_button = read_hi(LEFT_BUTTON_LIST)
    right_button = read_hi(RIGHT_BUTTON_LIST)
    engine_light = read_low(ENGINE_LIGHT_LIST)
    oil_light = read_low(OIL_LIGHT_LIST)
    return ([blinker_left, blinker_right, hi_beam, left_button, right_button, engine_light, oil_light])
      