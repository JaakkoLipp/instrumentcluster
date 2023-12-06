import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import math
import datetime 
import time
import requests # For frontend data transfer
from w1thermsensor import W1ThermSensor
import os

def analog_read(channel):

    # Spi pins:
    CLK = 11   
    MISO = 9
    MOSI = 10
    CS = 8
    mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
    adc_out = mcp.read_adc(channel)
    return adc_out

def read_volts_12(V12_READ_INPUTLIST, MULTIPLIER_12V): # ADC channel number (0-7) and multiplier from main
    data = analog_read(V12_READ_INPUTLIST)
    finaldata = (data / 1023) * (3.3 * MULTIPLIER_12V)
    return finaldata


def read_hi(channellist, HIREADLIMIT): # ADC channel number (0-7) and limit for highread from main
    data = analog_read(channellist)
    if data > HIREADLIMIT:
        finaldata = True
    else:
        finaldata = False
    return finaldata


def read_low(channellist, LOWREADLIMIT): # ADC channel number (0-7) and limit for lowread from main
    data = analog_read(channellist)
    if data < LOWREADLIMIT:
        finaldata = True
    else:
        finaldata = False
    return finaldata

def read_ambient_light(AMBIENT_LIGHT_LIST, NIGHTMODETHRESHOLD): # ADC channel number (0-7) and data limit (0-1023) for night mode from main
    data = analog_read(AMBIENT_LIGHT_LIST)
    if data > NIGHTMODETHRESHOLD:
        finaldata = True
    else:
        finaldata = False
    return finaldata

def read_ambient_temperature(AMBIENT_TEMP_PIN): # Pin which sensor is connected, BCM
    sensor = W1ThermSensor()
    data = sensor.get_temperature()
    temperature = round(data, 1)
    return temperature


def read_watertemperature(WATERTEMP_INPUT_LIST): # ADC channel number (0-7)
    multiplier =  10 # This value multiplies the temperature 
    data = analog_read(WATERTEMP_INPUT_LIST)
    resistance = (data / 1023) * (3.3 * multiplier)
    temperature = resistance -30.57 * math.log(resistance) + 212.11 # Function to get temperature from kawasaki anti linear stock water temperature sensor
    return temperature


def read_reservefuelstate(RESERVEFUEL_INPUT_LIST): # ADC channel number (0-7)
    Threshold = 0.206 # Activation value of fuel light 
    data = analog_read(RESERVEFUEL_INPUT_LIST)
    voltage = (1023 / data) * 3.3
    if voltage < Threshold:
        reservefuel = True
    else:
        reservefuel = False
    return reservefuel


def readstate(inputpin): # Reads state of gpio pin and returns True or False
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(inputpin, GPIO.OUT)
    GPIO.output(inputpin, GPIO.LOW)
    GPIO.setup(inputpin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    state = GPIO.input(inputpin)
    GPIO.cleanup()
    if state == 1:
        return True
    else:
        return False
    

def getspeed(SPEEDPIN, SPEEDRATIO, CORRECTION):
    # Set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SPEEDPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Initialize variables
    falling_edges = 0
    prev_time = None
    frequencies = []
    num_samples = 1
    sampler = 0
    loop_stop = False

    if CORRECTION == None:
        CORRECTION = 1.0
    try:
        while True:

            # Waits for the first falling edge

            if GPIO.wait_for_edge(SPEEDPIN, GPIO.FALLING, timeout=260) is None:  # If timeout occures, returns speed 0
                print("exited before getspeed loop")
                GPIO.cleanup()
                return [0, 0]
            # Measure time between falling edges
            if prev_time is not None:
                time_difference = time.time() - prev_time
                frequency = 1.0 / time_difference  # Calculate frequency
                frequencies.append(frequency)
                falling_edges += 1
                if sampler == 0:   # Going to run only once to determinate sample size
                    if frequency <=4: # At low speeds using smaller sample size for shorter sampling times
                        num_samples = 1
                    elif frequency > 4 and frequency < 8:
                        num_samples = 1
                    elif frequency >= 8 and frequency < 15:
                        num_samples = 2
                    elif frequency >= 15 and frequency < 40:
                        num_samples = 2
                    else:
                        num_samples = 3
                sampler = 1     # Rising sampler variable not to run sampler loop again
                
                # Exit after a specified number of samples
                if falling_edges >= num_samples:
                    print("calculating speed in getspeed")
                    final_frequency = sum(frequencies) / len(frequencies)
                    speed = final_frequency * SPEEDRATIO  # Converting frequency to kmh using speed ratio
                    corrected_speed = speed * CORRECTION  # Correcting speed for known measuring error
                    GPIO.cleanup()
                    print("gpio cleanup in getspeed")
                    return [corrected_speed, final_frequency]
            
            prev_time = time.time()
    
    except Exception:
        return [0,0]
    
    

def getrpm(RPM_PIN):
    # Set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RPM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Initialize variables
    falling_edges = 0
    prev_time = None
    frequencies = []
    num_samples = 2

    try:
        for x in range(num_samples):
            # Wait for the first falling edge
            if GPIO.wait_for_edge(RPM_PIN, GPIO.FALLING, timeout=60) is None:  # If timeout occures, returns rpm 0. Times out if rpm is lower than 500
                rpm = 0
                GPIO.cleanup()
                return rpm 
            
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
    
    

def get_gear_speed_and_rpm(RPM_PIN, NEUTRAL_LIGHT_LIST, FRONT_SPROCKET_PULSES_PER_ROTATION, GEAR_RATIO, GEAR_SENSITIVITY, LOWREADLIMIT, SPEEDPIN, SPEEDRATIO, CORRECTION): 
    # Returns list containing [str:gear, int:speed km/h, int:rpm]

    speedlist = getspeed(SPEEDPIN, SPEEDRATIO, CORRECTION)  # Gets speed and speed signal frequency
    speed = speedlist[0]
    speed_frequency = speedlist[1]

    rpm = getrpm(RPM_PIN)   # Gets rpm

    if (read_low(NEUTRAL_LIGHT_LIST, LOWREADLIMIT) == True): # Reads if neutral pin is low or not. If pin is low, N is returned
        return (["N", speed, rpm])
    else:

        front_sprocket_speed = (speed_frequency / FRONT_SPROCKET_PULSES_PER_ROTATION) * 60 # Change revolutions per second to rpm 
        clutch_rpm = rpm / 1.611 # Clutch / crank reduction ratio
        if front_sprocket_speed == 0:
            return (["-", speed, rpm])
        else:
            ratio = clutch_rpm / front_sprocket_speed
            for i in range(6):
                if (abs(ratio-GEAR_RATIO[i]) < GEAR_SENSITIVITY):
                    return ([str(i + 1), speed, rpm])
            return (["-", speed, rpm])
    

def get_status(BLINKER_LEFT_PIN, BLINKER_RIGHT_PIN,HI_BEAM_PIN, LEFT_BUTTON_LIST, RIGHT_BUTTON_LIST, ENGINE_LIGHT_PIN, OIL_LIGHT_PIN, BUTTONSLEEP, HIREADLIMIT, LOWREADLIMIT):  # status output 9 segment list: [blinker left, blinker right, hi beam, left button, right button, engine light, oil light, sceneshift, longpress]. when on, state is 1, when off state is 0 except in sceneshift where output can be -1, 0 or 1.
    blinker_left = readstate(BLINKER_LEFT_PIN)
    blinker_right = readstate(BLINKER_RIGHT_PIN)
    hi_beam = readstate(HI_BEAM_PIN)                                             # Current button interface:
    left_button = read_hi(LEFT_BUTTON_LIST, HIREADLIMIT)                         # Sceneshift = left button shortpress (sceneshift == -1)
    right_button = read_hi(RIGHT_BUTTON_LIST, HIREADLIMIT)                       # If scene resetted or interacted = left button longpress (longpress == -1)
    engine_light = readstate(ENGINE_LIGHT_PIN)
    oil_light = readstate(OIL_LIGHT_PIN)
    longpress = 0
    sceneshift = 0

    

    if left_button == True:                                                           
        time.sleep(BUTTONSLEEP / 3)
        if read_hi(LEFT_BUTTON_LIST, HIREADLIMIT) == True:
            time.sleep(BUTTONSLEEP / 3)
            if read_hi(LEFT_BUTTON_LIST, HIREADLIMIT) == True:                                                 
                time.sleep(BUTTONSLEEP / 3)                                                   
                left_buttonlongpress = read_hi(LEFT_BUTTON_LIST, HIREADLIMIT)                               
                if left_buttonlongpress == left_button:
                    longpress = -1   # For long left press. outputs -1
                    sceneshift = 0
                else:
                    sceneshift = -1  # For short left press to switch scene left
                    longpress = 0            
            else:
                sceneshift = -1      # For short left press to switch scene left
                longpress = 0
        else:
            sceneshift = -1          # For short left press to switch scene left
            LONGPRESS = 0

    elif right_button == True:
        time.sleep(BUTTONSLEEP)
        if True == read_hi(RIGHT_BUTTON_LIST, HIREADLIMIT):
            longpress = 1            # For long right press. outputs 1
            sceneshift = 0
        else: 
            sceneshift = 1           # For short right press to switch scene right
            longpress = 0
            
    else:
        sceneshift = 0 # Sceneshift does not shift scene
        longpress = 0  # No long press detected
    return ([blinker_left, blinker_right, hi_beam, left_button, right_button, engine_light, oil_light, sceneshift, longpress])

def otherdataread(AMBIENT_LIGHT_LIST, NIGHTMODETHRESHOLD, WATERTEMP_INPUT_LIST, RESERVEFUEL_INPUT_LIST): # Outputs list containing [nightmode 1/0, reservefuelstate 1/0, watertemperature string]
	nightmode = read_ambient_light(AMBIENT_LIGHT_LIST, NIGHTMODETHRESHOLD)           # Reads ambient light status, True or False
	reservefuelstate = read_reservefuelstate(RESERVEFUEL_INPUT_LIST)                 # Reads reservefuel state, True or False
	watertempint = read_watertemperature(WATERTEMP_INPUT_LIST)                       # Reada watertemperature
	watertemprounded = round(watertempint, 0)                                        # Rounds watertemperature to full number
	watertempstr = str(watertemprounded) + " c°"                                     # Makes watertemperature string and adds unit
	outputlist = [nightmode, reservefuelstate, watertempstr]                         # Makes output list
	return outputlist
	

def odoread():
    with open("odo.txt", "r") as file:
        odoread = file.read()
        file.close()
        floatodoread = float(odoread)
        return floatodoread

def tripread():
    with open("trip.txt", "r") as file:
        tripread = file.read()
        file.close()
        floattripread = float(tripread)
        return floattripread


def odowrite(odo):
    try: # Try to open "odo.txt" for writing
        stringodo = str(odo)
        with open("odo.txt", "w") as file:
            file.write(stringodo)
            file.close()
        return

    except FileNotFoundError:
        stringodo = str(odo)
        with open("backup.txt", "w") as file:   # If the file doesn't exist, creates "backup.txt" and saves "odo" there
            file.write(stringodo)               
            file.close()
        return
        

    except Exception as e:
        print(f"An error occurred with odowrite: {e}")
        return

def tripwrite(trip):
    try: # Try to open "trip.txt" for writing
        stringtrip = str(trip)
        with open("trip.txt", "w") as file:
            file.write(stringtrip)
            file.close()
        return
    except Exception as e:
        print(f"An error occurred with tripwrite: {e}")
        return

def sceneshifter(getstatus, scene, SCENEMAX):
    if getstatus[7] == -1:
        if scene < SCENEMAX and scene >= 1:
            scene = scene + 1
            return scene # Returns scene which is active after button input
        else:	
            scene = 1
            return scene # Returns scene which is active after button input if SCENEMAX is reached
    else:
        return scene     # Returns scene which is active without button input


def scenedrawer(scene, getstatus, odo, trip, qs_status, QS_PIN, V12_READ_INPUTLIST, MULTIPLIER_12V, AMBIENT_TEMP_PIN):

    # Subprogram outputs string which should be displayed in free area of instrument cluster as list, item0 is string and item1 changes to values
    # Scenecounter starting from scene 2 to make odometer default display if error occures

    if scene == 2: # Trip meter scene
        roundtrip = round(trip, 1)          # Rounding trip to 1 decimal in km
        tripstring = str(roundtrip) + " km" # Converting trip to string and add km unit
        if getstatus[8] == -1:
            trip = 0.0                      # If trip reset pressed, set trip to 0
        triplist = [tripstring, trip]       # Returns list including value and changes.
        return triplist	
    
    elif scene == 3: # Ambient temperature scene
        ambient_temp = read_ambient_temperature(AMBIENT_TEMP_PIN) # Reads ambient temperature from adc	
        ambientround = round(ambient_temp, 1)                     # rounding ambient temp to 1 decimal
        ambientstring = str(ambientround) + " c°"                 # converting ambient temp to string and adding unit 
        return [ambientstring]
    
    elif scene == 4: # Battery voltage scene
        bat_volt = read_volts_12(V12_READ_INPUTLIST, MULTIPLIER_12V)   # Read voltgae from adc 
        voltage = round(bat_volt, 1)                                   # Makes voltages to 1 decimal
        voltagestring = str(voltage) + " V"                            # Makes voltage as string and adds "v"
        return [voltagestring]
    
    elif scene == 5: # Quickshifter controlling scene
        if getstatus[8] == -1: # If left button long press detected
            if qs_status == 1: # If qs enabled, turn pin low to disable qs and set qs_status = 0
                GPIO.setmode(GPIO.BCM
        )
                GPIO.setup(QS_PIN, GPIO.OUT)
                GPIO.output(QS_PIN, GPIO.LOW) # Set gpio to low for relay to be in active state
                GPIO.cleanup()
                qs_status = 0  # Set qs status to 0, disabled
            else:              # If qs diabled, turn pin high to activate qs and set qs_status = 1
                GPIO.setmode(GPIO.BCM
        )
                GPIO.setup(QS_PIN, GPIO.OUT)
                GPIO.output(QS_PIN, GPIO.HIGH) # Set gpio to high for relay to be in not active state
                GPIO.cleanup()
                qs_status = 1 # Set qs status to 1, activated
        
        if qs_status == 1:
            qs_status_string = "Quickshifter enabled."
        else: 
            qs_status_string = "Quickshifter disabled."
        
        return [qs_status_string, qs_status]
        
    elif scene == 6: # Timer scene
        return ["Timer not defined yet."]

    elif scene == 7: # Bt audio scene
        return ["BT audio not defined yet."]  # Output string to report bt audio not defined

    else:		 # Odometer scene
        odoround = round(odo, 0)
        odostring = str(odoround) + " km"
        return [odostring]
    

def send_data_and_calc_odo(odotime, gear_speed_rpm, status, sceneout, otherdata):
    speedinkmh = gear_speed_rpm[1]      # 2. item in list is speed in km/h
    speedinms = speedinkmh / 3.6        # Convert speed to m/s
    deltatime = time.time() - odotime   # Calculate time difference between 1.st and 2.nd speed sending
    distance = speedinms * deltatime    # Calculate distance covered in that time with current speed
    distanceinkm = distance / 1000.0
    dt_string = time.strftime("%H:%M")  # Time to display
    server_input_list = [gear_speed_rpm[0], gear_speed_rpm[1], gear_speed_rpm[2], status[0], 
                         status[1], status[2], status[5], status[6], sceneout, dt_string, 
                         otherdata[0], otherdata[1], otherdata[2]]

    #################################API########################################
    data = {"GPIOLIST": server_input_list}

    try:
        response = requests.post("http://localhost:5000/gpiodata", json=data)
        # Checking if request was succesfull
        if response.status_code == 200:
            print("Data sent successfully!", data)
        else:
            print("Failed to send data. Status code:", response.status_code)

    except requests.exceptions.RequestException as e:
        # Catching any exception raised by the requests library
        print("Data sentn't: ", e)

    #################################API########################################

    newtime = time.time()            # New time for next distance calculation
    output = [distanceinkm, newtime] # Output time for next loop and distance to add to the odo and trip.
    return output
	

def shutdownwrite(odo, trip):
	odowrite(odo)
	tripwrite(trip)
	return
