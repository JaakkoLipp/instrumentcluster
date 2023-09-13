#ADC read test
import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0
spi.max_speed_hz = 1350000  # MCP3008 supports a clock speed up to 3.6 MHz
def read_adc(channel):
    if channel < 0 or channel > 7:
        raise ValueError("Invalid channel. Channel must be 0-7.")
    
    # MCP3008 command format: 0b0000XXXX, where XXXX is the channel (0-7)
    command = [0x01, (8 + channel) << 4, 0x00]
    
    response = spi.xfer2(command)
    
    # Parse the response (12 bits of data in the second and third bytes)
    adc_value = ((response[1] & 0x0F) << 8) + response[2]
    
    return adc_value
channel = 0
adc_value = read_adc(channel)
print(f"ADC Value on Channel {channel}: {adc_value}")
spi.close()
