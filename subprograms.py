import RPi.GPIO as GPIO
import spidev
import math
import datetime 
import time


def analog_read(channel):
    spi = spidev.SpiDev()
    spi.open(0, 0)
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    adc_out = ((r[1]&3) << 8) + r[2]
    return adc_out

def read_volts_12(V12_READ_INPUTLIST, MULTIPLIER_12V): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    data = analog_read(V12_READ_INPUTLIST)
    finaldata = (data / 1023) * (3.3 * MULTIPLIER_12V)
    return finaldata


def read_hi(channellist, HIREADLIMIT): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    data = analog_read(channellist)
    if data > HIREADLIMIT:
        finaldata = True
    else:
        finaldata = False
    return finaldata


def read_low(channellist, LOWREADLIMIT): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    data = analog_read(channellist)
    if data < LOWREADLIMIT:
        finaldata = True
    else:
        finaldata = False
    return finaldata

def read_ambient_light(AMBIENT_LIGHT_LIST, NIGHTMODETHRESHOLD): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    multiplier = 10
    data = analog_read(AMBIENT_LIGHT_LIST)
    resistance = (data / 1023) * (3.3 * multiplier)
    light_level = resistance #TODO check light level resistance curve to use!!!
    if light_level > NIGHTMODETHRESHOLD:
        finaldata = True
    else:
        finaldata = False
    return finaldata

def read_ambient_temperature(AMBIENT_TEMP_LIST): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    multiplier = 10
    data = analog_read(AMBIENT_TEMP_LIST)
    resistance = (data / 1023) * (3.3 * multiplier)
    temperature = resistance #TODO check ambient temperature probe resistance curve to use!!!
    return temperature


def read_watertemperature(WATERTEMP_INPUT_LIST): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    multiplier =  10
    data = analog_read(WATERTEMP_INPUT_LIST)
    resistance = (data / 1023) * (3.3 * multiplier)
    temperature = resistance # TODO remove !!-30.57 * math.log(resistance) + 212.11 #function to get temperature from kawasaki stock water temperature sensor
    return temperature


def read_reservefuelstate(RESERVEFUEL_INPUT_LIST): #"/dev/spidev1.0" tai "/dev/spidev1.1" , channel 0-7
    multiplier = 10
    data = analog_read(RESERVEFUEL_INPUT_LIST)
    resistance = (data / 1023) * (3.3 * multiplier)
    if resistance < 22: #activation value of reservefuel light 
        reservefuel = True
    else:
        reservefuel = False
    return reservefuel


def readstate(inputpin):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(inputpin, GPIO.OUT)
    GPIO.output(inputpin, GPIO.LOW)
    state = GPIO.input(inputpin)
    if state == 1:
        return True
    else:
        return False
    

def getspeed(SPEEDPIN, SPEEDRATIO, CORRECTION):
    # Set up GPIO
    GPIO.setmode(GPIO.BOARD)
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
            # Wait for the first falling edge
            
            
            if GPIO.wait_for_edge(SPEEDPIN, GPIO.FALLING, timeout=260) is None:  #if timeout occures, return speed 0
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
                    print("calculating speed in getspeed")
                    final_frequency = sum(frequencies) / len(frequencies)
                    speed = final_frequency * SPEEDRATIO  # Converting frequency to kmh using speed ratio
                    corrected_speed = speed * CORRECTION # Correcting speed for known measuring error
                    GPIO.cleanup()
                    print("gpio cleanup in getspeed")
                    return [corrected_speed, final_frequency]
            
            prev_time = time.time()
    
    except KeyboardInterrupt:
        pass
    
    

def getrpm(RPM_PIN):
    # Set up GPIO
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(RPM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
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
    
    

def get_gear_speed_and_rpm(RPM_PIN, NEUTRAL_LIGHT_LIST, FRONT_SPROCKET_PULSES_PER_ROTATION, GEAR_RATIO, GEAR_SENSITIVITY, LOWREADLIMIT, SPEEDPIN, SPEEDRATIO, CORRECTION): #returns list containing [str:gear, int:speed km/h, int:rpm]
    
    speedlist = getspeed(SPEEDPIN, SPEEDRATIO, CORRECTION)  #gets speed and speed signal frequency
    speed = speedlist[0]
    speed_frequency = speedlist[1]

    rpm = getrpm(RPM_PIN)   #gets rpm

    if (read_low(NEUTRAL_LIGHT_LIST, LOWREADLIMIT) == True): #reads if neutral pin low or not. If low N is displayed.
        return (["N", speed, rpm])
    else:

        front_sprocket_speed = (speed_frequency / FRONT_SPROCKET_PULSES_PER_ROTATION) * 60 # Change revolutions per second to rpm 
        clutch_rpm = rpm / 1.611 # clutch / crank reduction ratio
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
    hi_beam = readstate(HI_BEAM_PIN)                                 #current button interface:
    left_button = read_hi(LEFT_BUTTON_LIST, HIREADLIMIT)                         #sceneshift = left button shortpress (sceneshift == -1)
    right_button = read_hi(RIGHT_BUTTON_LIST, HIREADLIMIT)                       #in scene reset or interact = left button longpress (longpress == -1)
    engine_light = readstate(ENGINE_LIGHT_PIN)
    oil_light = readstate(OIL_LIGHT_PIN)

    

    if left_button == True:                                                           
        time.sleep(BUTTONSLEEP / 3)
        if read_hi(LEFT_BUTTON_LIST, HIREADLIMIT) == True:
            time.sleep(BUTTONSLEEP / 3)
            if read_hi(LEFT_BUTTON_LIST, HIREADLIMIT) == True:                                                 
                time.sleep(BUTTONSLEEP / 3)                                                   
                left_buttonlongpress = read_hi(LEFT_BUTTON_LIST, HIREADLIMIT)                               
                if left_buttonlongpress == left_button:
                    longpress = -1 #for long left press. outputs -1
                    sceneshift = 0
                else:
                    sceneshift = -1 # for short left press to switch scene left
                    longpress = 0            
            else:
                sceneshift = -1 # for short left press to switch scene left
                longpress = 0
        else:
            sceneshift = -1 # for short left press to switch scene left
            LONGPRESS = 0

    elif right_button == True:
        time.sleep(BUTTONSLEEP)
        if True == read_hi(RIGHT_BUTTON_LIST, HIREADLIMIT):
            longpress = 1 #for long right press. outputs 1
            sceneshift = 0
        else: 
            sceneshift = 1 # for short right press to switch scene right
            longpress = 0
            
    else:
        sceneshift = 0 # Sceneshift does not shift scene
        longpress = 0 # No long press detected

    return ([blinker_left, blinker_right, hi_beam, left_button, right_button, engine_light, oil_light, sceneshift, longpress])

def otherdataread(AMBIENT_LIGHT_LIST, NIGHTMODETHRESHOLD, WATERTEMP_INPUT_LIST, RESERVEFUEL_INPUT_LIST): #Outputs list containing [nightmode 1/0, reservefuelstate 1/0, watertemperature string]
	nightmode = read_ambient_light(AMBIENT_LIGHT_LIST, NIGHTMODETHRESHOLD)           #read ambient light status, 1 or 0
	reservefuelstate = read_reservefuelstate(RESERVEFUEL_INPUT_LIST) # read reservefuel state, 1 or 0
	watertempint = read_watertemperature(WATERTEMP_INPUT_LIST)     #read watertemperature
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

def sceneshifter(getstatus, scene, SCENEMAX):
    if getstatus[7] == -1:
        if scene < SCENEMAX and scene >= 1:
            scene = scene + 1
            return scene # returns scene which is active after button input
        else:	
            scene = 1
            return scene # returns scene which is active after button input
    else:
        return scene # returns scene which is active without button input


def scenedrawer(scene, getstatus, odo, trip, qs_status, QS_PIN, V12_READ_INPUTLIST, MULTIPLIER_12V, AMBIENT_TEMP_LIST): #subprogram outputs string which should be displayed in changing slot as list, item0 is string and item1 changes to values
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
        ambient_temp = read_ambient_temperature(AMBIENT_TEMP_LIST) # readambient from adc	
        ambientround = round(ambient_temp, 1)     # rounding ambient temp to 1 decimal
        ambientstring = str(ambientround) + " c°" # converting ambient temp to string and add unit 
        return [ambientstring]
    
    elif scene == 4: # scene battery voltage display
        bat_volt = read_volts_12(V12_READ_INPUTLIST, MULTIPLIER_12V)           # readvolts from adc 
        voltage = round(bat_volt, 1)         # make voltages to 1 decimal
        voltagestring = str(voltage) + " V"  # make voltage as string and add "v"
        return [voltagestring]
    
    elif scene == 5: # scene for controlling quickshifter status
        if getstatus[8] == -1: # if left button long press detected
            if qs_status == 1: # if qs enabled, turn pin low to disable qs and set qs_status = 0
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(QS_PIN, GPIO.OUT)
                GPIO.output(QS_PIN, GPIO.LOW) # set gpio to low for relay to be in active state
                GPIO.cleanup()
                qs_status = 0  # set qs status to 0, disabled
            else:              # if qs diabled, turn pin high to activate qs and set qs_status = 1
                GPIO.setmode(GPIO.BOARD)
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
    dt_string = time.strftime("%H:%M") #Time to display
    server_input_list = [gear_speed_rpm[0], gear_speed_rpm[1], gear_speed_rpm[2], status[0], status[1], status[2], status[5], status[6], sceneout, dt_string, otherdata[0], otherdata[1], otherdata[2]]

    #TODO jaakko plox remov hastags
    #data = {"GPIOLIST": server_input_list}
    #response = requests.post("localhost:5000/gpiodata", json=data)
    #print("Data sent!!", data)

    newtime = time.time() # new time for next distance calculation
    output = [distanceinkm, newtime] # output time for next loop and distance to add to the odo and trip.
    return output
	

def shutdownwrite(odo, trip):
	odowrite(odo)
	tripwrite(trip)
	return
