import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import math as mt
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

def read_ambient_temperature():
    return round(W1ThermSensor().get_temperature(), 1)



def read_watertemperature(WATERTEMP_INPUT_LIST): # ADC channel number (0-7)
    data = analog_read(WATERTEMP_INPUT_LIST)

    if data < 5 or data > 1022 or data == 0: # if ADC value under 5, thermistor is not connected properly
        return("N/A")

    resistance = 330 / (1023/ data - 1) 
   
    # Function to get temperature from kawasaki thermistor

    A = 1.775685151e-3
    B = 2.537279638e-4
    C = -2.461770337e-7

    # Steinhart - Hart Equation
    TempK = 1 / (A + (B * mt.log(resistance)) + C * mt.pow(mt.log(resistance),3))
    # Convert from Kelvin to Celsius
    TempC = round(TempK - 273.15 ,0)

    return TempC




def read_reservefuelstate(RESERVEFUEL_INPUT_LIST): # ADC channel number (0-7) #TODO elias
    Threshold = 0.206 # Activation value of fuel light 
    data = analog_read(RESERVEFUEL_INPUT_LIST)
    voltage = (1023 / data) * 3.3
    if voltage < Threshold: 
        reservefuel = True
    else:
        reservefuel = False
    return reservefuel


def readstate(inputpin):
    try:
        state = GPIO.input(inputpin)
        return state == 0
    except Exception as e:
        print(f"Error reading GPIO pin {inputpin}: {e}")
        return False\
        
def pin_changed_callback(channel):
    data = GPIO.input(channel)
    if data:
        output = True 
    else:
        output = False

    #TODO jaakko aplly datasend here
    # channels are 3, 6 and 13, which are 
    # left blinker, right blinker and high beam
    

def getspeed(SPEEDPIN, SPEEDRATIO, CORRECTION):
    
    # Initialize variables
    falling_edges = 0
    prev_time = None
    frequencies = []
    num_samples = 1
    sampler = 0
    
    if CORRECTION is None:
        CORRECTION = 1.0

    try:
        while True:
            if GPIO.wait_for_edge(SPEEDPIN, GPIO.FALLING, timeout=260) is None:
                print("Exited before getspeed loop")
                break
            
            if prev_time is not None:
                time_difference = time.time() - prev_time
                frequency = 1.0 / time_difference
                
                if 4 <= frequency < 8:
                    num_samples = 1
                elif 8 <= frequency < 40:
                    num_samples = 2
                elif frequency >= 40:
                    num_samples = 3
                
                if sampler == 0:
                    sampler = 1
                    # Exit after a specified number of samples
                    if falling_edges >= num_samples - 1:
                        final_frequency = sum(frequencies) / len(frequencies)
                        speed = final_frequency * SPEEDRATIO
                        corrected_speed = round(speed * CORRECTION ,0)
                        return [corrected_speed, final_frequency]
                
                falling_edges += 1
                frequencies.append(frequency)
            
            prev_time = time.time()
    
    except Exception as e:
        print(f"Error in getspeed: {e}")
    
    
    return [0, 0]
    

def getrpm(RPM_PIN):
    
    # Initialize variables
    falling_edges = 0
    prev_time = None
    frequencies = []
    num_samples = 5
    rpm = 0

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
    
    

def get_gear_speed_and_rpm(RPM_PIN, NEUTRAL_LIGHT_LIST, FRONT_SPROCKET_PULSES_PER_ROTATION, GEAR_RATIO, GEAR_SENSITIVITY, LOWREADLIMIT, SPEEDPIN, SPEEDRATIO, CORRECTION):
    # Returns list containing [str:gear, int:speed km/h, int:rpm]

    speed, speed_frequency = getspeed(SPEEDPIN, SPEEDRATIO, CORRECTION)  # Gets speed and speed signal frequency
    rpm = getrpm(RPM_PIN)   # Gets rpm

    if read_low(NEUTRAL_LIGHT_LIST, LOWREADLIMIT):
        return ["N", speed, rpm]

    front_sprocket_speed = (speed_frequency / FRONT_SPROCKET_PULSES_PER_ROTATION) * 60  # Convert revolutions per second to rpm
    clutch_rpm = rpm / 1.611  # Clutch / crank reduction ratio

    if front_sprocket_speed == 0:
        return ["-", speed, rpm]

    ratio = clutch_rpm / front_sprocket_speed
    for i in range(6):
        if abs(ratio - GEAR_RATIO[i]) < GEAR_SENSITIVITY:
            return [str(i + 1), speed, rpm]

    return ["-", speed, rpm]
    

def get_status(LEFT_BUTTON_LIST, RIGHT_BUTTON_LIST, ENGINE_LIGHT_PIN, OIL_LIGHT_PIN, BUTTONSLEEP, HIREADLIMIT):  # status output 9 segment list: [blinker left, blinker right, hi beam, left button, right button, engine light, oil light, sceneshift, longpress]. when on, state is 1, when off state is 0 except in sceneshift where output can be -1, 0 or 1.                                             # Current button interface:
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
    return ([left_button, right_button, engine_light, oil_light, sceneshift, longpress])

def otherdataread(AMBIENT_LIGHT_LIST, NIGHTMODETHRESHOLD, WATERTEMP_INPUT_LIST, RESERVEFUEL_INPUT_LIST): # Outputs list containing [nightmode 1/0, reservefuelstate 1/0, watertemperature string]
	nightmode = read_ambient_light(AMBIENT_LIGHT_LIST, NIGHTMODETHRESHOLD)           # Reads ambient light status, True or False
	reservefuelstate = read_reservefuelstate(RESERVEFUEL_INPUT_LIST)                 # Reads reservefuel state, True or False
	watertemprounded = read_watertemperature(WATERTEMP_INPUT_LIST)                   # Reads watertemperature
	watertempstr = str(watertemprounded) + " c°"                                     # Makes watertemperature string and adds unit
	outputlist = [nightmode, reservefuelstate, watertempstr]                         # Makes output list
	return outputlist
	

def odoread():
    with open("odo.txt", "r") as file:
        return float(file.read())

def tripread():
    with open("trip.txt", "r") as file:
        return float(file.read())


def odowrite(odo):
    stringodo = str(odo)
    try:
        with open("odo.txt", "w") as file:
            file.write(stringodo)

    except FileNotFoundError:
        # If "odo.txt" doesn't exist, creates "backup.txt" and saves "odo" there
        with open("backup.txt", "w") as file:
            file.write(stringodo)

    except Exception as e:
        print(f"An error occurred with odowrite: {e}")

def tripwrite(trip):
    try:
        with open("trip.txt", "w") as file:
            file.write(str(trip))
    except Exception as e:
        print(f"An error occurred with tripwrite: {e}")

def sceneshifter(getstatus, scene, SCENEMAX):
    if getstatus[4] == -1:
        if scene < SCENEMAX and scene >= 1:
            scene = scene + 1
            return scene # Returns scene which is active after button input
        else:	
            scene = 1
            return scene # Returns scene which is active after button input if SCENEMAX is reached
    else:
        return scene     # Returns scene which is active without button input


def scenedrawer(scene, getstatus, odo, trip, qs_status, QS_PIN, V12_READ_INPUTLIST, MULTIPLIER_12V):

    # Subprogram outputs string which should be displayed in free area of instrument cluster as list, item0 is string and item1 changes to values
    # Scenecounter starting from scene 2 to make odometer default display if error occures

    if scene == 2: # Trip meter scene
        roundtrip = round(trip, 1)          # Rounding trip to 1 decimal in km
        tripstring = str(roundtrip) + " km" # Converting trip to string and add km unit
        if getstatus[5] == 1:
            trip = 0.0                      # If trip reset pressed, set trip to 0
        triplist = [tripstring, trip]       # Returns list including value and changes.
        return triplist	
    
    elif scene == 3: # Ambient temperature scene
        ambient_temp = read_ambient_temperature() # Reads ambient temperature from adc	
        ambientstring = str(ambient_temp) + " c°"                 # converting ambient temp to string and adding unit 
        return [ambientstring]
    
    elif scene == 4: # Battery voltage scene
        bat_volt = read_volts_12(V12_READ_INPUTLIST, MULTIPLIER_12V)   # Read voltgae from adc 
        voltage = round(bat_volt, 1)                                   # Makes voltages to 1 decimal
        voltagestring = str(voltage) + " V"                            # Makes voltage as string and adds "v"
        return [voltagestring]
    
    elif scene == 5: # Quickshifter controlling scene
        if getstatus[5] == 1: # If left button long press detected
            GPIO.setup(QS_PIN, GPIO.OUT)
            if qs_status == 1: # If qs enabled, turn pin low to disable qs and set qs_status = 0
        
                GPIO.output(QS_PIN, GPIO.LOW) # Set gpio to low for relay to be in active state
                qs_status = 0  # Set qs status to 0, disabled
            else:              # If qs diabled, turn pin high to activate qs and set qs_status = 1
        
                GPIO.output(QS_PIN, GPIO.HIGH) # Set gpio to high for relay to be in not active state
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
    server_input_list = [gear_speed_rpm[0], gear_speed_rpm[1], status[2], status[3], sceneout, dt_string, 
                         otherdata[0], otherdata[1], otherdata[2]]
    #geardata str, speedata int, engine_light bool, oil_light bool, scene str, clock time str, nightmode bool, reservefuelstate bool, watertempstr

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
    GPIO.cleanup()
    return
