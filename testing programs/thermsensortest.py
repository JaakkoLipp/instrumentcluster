from w1thermsensor import W1ThermSensor
from time import sleep

def read_ambient_temperature(): # Pin which sensor is connected, BCM
    sensor = W1ThermSensor()
    data = sensor.get_temperature()
    temperature = round(data, 1)
    return temperature

while True:
    print(read_ambient_temperature())
    