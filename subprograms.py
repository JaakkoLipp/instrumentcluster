import time
import math
#import spi #TODO import spi
from datetime import datetime
import requests
import RPi.GPIO as GPIO

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
        finaldata = True
    else:
        finaldata = False
    return finaldata


def read_low(devicechannellist): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    device = devicechannellist[0]
    channel = devicechannellist[1]
    status = spi.openSPI(device, speed=1000000)
    adc = spi.transfer((1,(8+channel)<<4,0))
    data = ((adc[1]&3) << 8) + adc[2]
    spi.close()
    if data < LOWREADLIMIT:
        finaldata = True
    else:
        finaldata = False
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
    if light_level > NIGHTMODETHRESHOLD:
        finaldata = True
    else:
        finaldata = False
    return finaldata

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
    temperature = -30.57 * math.log(resistance) + 212.11 #function to get temperature from kawasaki stock water temperature sensor
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
    if resistance < 22: #activation value of reservefuel light 
        reservefuel = True
    else:
        reservefuel = False
    return reservefuel


def getspeed():
    # Set up GPIO
    GPIO.setmode(GPIO.BOARD)
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
                    elif frequency > 4 and frequency < 8:
                        num_samples = 1
                    elif frequency >= 8 and frequency < 15:
                        num_samples = 2
                    elif frequency >= 15 and frequency < 40:
                        num_samples = 2
                    else:
                        num_samples = 3
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
    

def getrpm():
    # Set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SPEEDPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Initialize variables
    falling_edges = 0
    prev_time = None
    frequencies = []
    num_samples = 2

    try:
        for x in range(num_samples):
            # Wait for the first falling edge
            if GPIO.wait_for_edge(RPM_PIN, GPIO.FALLING, timeout=60) is None:  #if timeout occures, return rpm 0 and times out if rpm is lower than 500
                rpm = 0
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
    
    

def get_gear_speed_and_rpm(): #returns list containing [str:gear, int:speed km/h, int:rpm]
    
    speedlist = getspeed()  #gets speed and speed signal frequency
    speed = speedlist[0]
    speed_frequency = speedlist[1]

    rpm = getrpm(RPM_PIN)   #gets rpm

    if (read_low(NEUTRAL_LIST) == True): #reads if neutral pin low or not. If low N is displayed.
        return (["N", speed, rpm])
    else:

        front_sprocket_speed = (speed_frequency / FRONT_SPROCKET_PULSES_PER_ROTATION) * 60 # Change revolutions per second to rpm 
        clutch_rpm = rpm / 1.611 # clutch / crank reduction ratio
        ratio = clutch_rpm / front_sprocket_speed
        for i in range(6):
            if (abs(ratio-GEAR_RATIO[i]) < GEAR_SENSITIVITY):
                return ([str(i + 1), speed, rpm])
        return (["-", speed, rpm])
    

def get_status():  # status output 9 segment list: [blinker left, blinker right, hi beam, left button, right button, engine light, oil light, sceneshift, longpress]. when on, state is 1, when off state is 0 except in sceneshift where output can be -1, 0 or 1.
    blinker_left = read_hi(BLINKER_LEFT_LIST)
    blinker_right = read_hi(BLINKER_RIGHT_LIST)
    hi_beam = read_hi(HI_BEAM_LIST)                                 #current button interface:
    left_button = read_hi(LEFT_BUTTON_LIST)                         #sceneshift = left button shortpress (sceneshift == -1)
    right_button = read_hi(RIGHT_BUTTON_LIST)                       #in scene reset or interact = left button longpress (longpress == -1)
    engine_light = read_low(ENGINE_LIGHT_LIST)
    oil_light = read_low(OIL_LIGHT_LIST)

    if left_button == True:                                                           
        time.sleep(BUTTONSLEEP / 3)
        if read_hi(LEFT_BUTTON_LIST) == True:
            time.sleep(BUTTONSLEEP / 3)
            if read_hi(LEFT_BUTTON_LIST) == True:                                                 
                time.sleep(BUTTONSLEEP / 3)                                                   
                left_buttonlongpress = read_hi(LEFT_BUTTON_LIST)                               
                if left_buttonlongpress == left_button:
                    longpress = -1 #for long left press. outputs -1
                else:
                    sceneshift = -1 # for short left press to switch scene left            
            else:
                sceneshift = -1 # for short left press to switch scene left
        else:
            sceneshift = -1 # for short left press to switch scene left

    elif right_button == True:
        time.sleep(BUTTONSLEEP)
        right_buttonlongpress = read_hi(RIGHT_BUTTON_LIST)
        if right_buttonlongpress == right_button:
            longpress = 1 #for long right press. outputs 1
        else: 
            sceneshift = 1 # for short right press to switch scene right
            
    else:
        sceneshift = 0 # Sceneshift does not shift scene
        longpress = 0 # No long press detected

    return ([blinker_left, blinker_right, hi_beam, left_button, right_button, engine_light, oil_light, sceneshift, longpress])

def otherdataread(): #Outputs list containing [nightmode 1/0, reservefuelstate 1/0, watertemperature string]
	nightmode = read_ambient_light()           #read ambient light status, 1 or 0
	reservefuelstate = read_reservefuelstate() # read reservefuel state, 1 or 0
	watertempint = read_watertemperature()     #read watertemperature
	watertemprounded = round(watertempint, 0)  # round watertemperature to full number
	watertempstr = str(watertemprounded) + " c°" # make watertemperature string and add unit
	outputlist = [nightmode, reservefuelstate, watertempstr] #make output list
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
        with open("backup.txt", "w") as file:   # If the file doesn't exist, create "backup.txt" and save "odo" there
            file.write(stringodo)               #TODO crontab file backup (Jaakko???)
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

def sceneshifter(getstatus, scene):
    if getstatus[7] == -1:
        if scene < SCENEMAX and scene >= 1:
            scene = scene + 1
            return scene # returns scene which is active after button input
        else:	
            scene = 1
            return scene # returns scene which is active after button input
    else:
        return scene # returns scene which is active without button input


def scenedrawer(scene, getstatus, odo, trip, qs_status): #subprogram outputs string which should be displayed in changing slot as list, item0 is string and item1 changes to values
	#TODO when using scenedrawer, must check for list to reset odo
	# scenecounter starting from 2 to make odometer default display if error occures

    if scene == 2: # scene tripmeter display
        roundtrip = round(trip, 1)          # rounding trip to 1 decimal in km
        tripstring = str(roundtrip) + " km" # converting trip to string and add km unit
        if getstatus[8] == -1:
            trip = 0.0  # if trip reset pressed, set trip to 0
        triplist = [tripstring, trip] # return list including value and changes.
        return triplist	
    
    elif scene == 3: # scene outside air temperature display
        ambient_temp = read_ambient_temperature() # readambient from adc	
        ambientround = round(ambient_temp, 1)     # rounding ambient temp to 1 decimal
        ambientstring = str(ambientround) + " c°" # converting ambient temp to string and add unit 
        return [ambientstring]
    
    elif scene == 4: # scene battery voltage display
        bat_volt = read_volts_12()           # readvolts from adc 
        voltage = round(bat_volt, 1)         # make voltages to 1 decimal
        voltagestring = str(voltage) + " V"  # make voltage as string and add "v"
        return [voltagestring]
    
    elif scene == 5: # scene for controlling quickshifter status
        if getstatus[8] == -1: # if left button long press detected
            if qs_status == 1: # if qs enabled, turn pin low to disable qs and set qs_status = 0
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(QS_PIN, GPIO.OUT)
                GPIO.output(QS_PIN, GPIO.LOW) # set gpio to low for relay to be in active state
                GPIO.cleanup()
                qs_status = 0  # set qs status to 0, disabled
            else:              # if qs diabled, turn pin high to activate qs and set qs_status = 1
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(QS_PIN, GPIO.OUT)
                GPIO.output(QS_PIN, GPIO.HIGH) # set gpio to high for relay to be in not active state
                GPIO.cleanup()
                qs_status = 1 #set qs status to 1, activated
        
        if qs_status == 1:
            qs_status_string = "Quickshifter enabled."
        else: 
            qs_status_string = "Quickshifter disabled."
        
        return [qs_status_string, qs_status]
        

    
    elif scene == 6: # scene timer, timer display
        return ["Timer not defined yet."]

    elif scene == 7: # scene bt audio metadata
        return ["BT audio not defined yet."]  # output string to report bt audio not setted up

    else:		 # scene odometer display
        odoround = round(odo, 0)
        odostring = str(odoround) + " km"
        return [odostring]

def send_data_and_calc_odo(odotime, gear_speed_rpm, status, sceneout, otherdata):
    speedinkmh = gear_speed_rpm[1] # 2. item in list is speed in km/h
    speedinms = speedinkmh / 3.6   # convert speed in to m/s
    deltatime = time.time() - odotime # calculate time difference between 1.st and 2.nd speed sending
    distance = speedinms * deltatime # calculate distance covered in that time with current speed
    distanceinkm = distance / 1000.0
    now = datetime.now()  # get time to display
    dt_string = now.strftime("%H:%M")
    server_input_list = [gear_speed_rpm[0], gear_speed_rpm[1], gear_speed_rpm[2], status[0], status[1], status[2], status[5], status[6], sceneout, dt_string, otherdata[0], otherdata[1], otherdata[3]]

    data = {"GPIOLIST": server_input_list}
    response = requests.post("localhost:5000/gpiodata", json=data)
    print("Data sent!!", data)

    newtime = time.time() # new time for next distance calculation
    output = [distanceinkm, newtime] # output time for next loop and distance to add to the odo and trip.
    return output
	

def shutdownwrite(odo, trip):
	odowrite(odo)
	tripwrite(trip)
	return
