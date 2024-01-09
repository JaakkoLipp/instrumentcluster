import RPi.GPIO as GPIO
import spidev
import time

def analog_read(channel):
    spi = spidev.SpiDev()
    spi.open(0, 0)
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    adc_out = ((r[1]&3) << 8) + r[2]
    spi.close()
    return adc_out

# spi channels:
channel1 = 0
channel2 = 1
channel3 = 2
channel4 = 3
channel5 = 4
channel6 = 5
channel7 = 6 #NEGATIVE READ!!
channel8 = 7 #NEGATIVE READ!!

while True:

    a = analog_read(channel1)
    b = analog_read(channel2)
    c = analog_read(channel3)
    d = analog_read(channel4) 
    e = analog_read(channel5) 
    f = analog_read(channel6) 
    g = analog_read(channel7)
    h = analog_read(channel8) 

    print(a, b, c, d, e, f, g, h)
    time.sleep(1)