# send start message
# print on screen for 2 minutes
# send stop message


# cyrus , colin, grant 2021

import board
import busio
import displayio
import terminalio
from time import sleep
import time

from adafruit_display_text import label
import adafruit_displayio_sh1107
from digitalio import DigitalInOut, Direction, Pull
import digitalio

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from adafruit_bluefruit_connect.packet import Packet

import ulora
import adafruit_rfm9x

DEBUG = 1                   # In debug mode we just listen and forward
"""
Constant parameters
"""
# LED DISPLAY
WIDTH = 128
HEIGHT = 64
BORDER = 2

screen_refresh = 30         # time interval (s) for rewriting screen (mainly for RSSI)

# RADIO MESSAGES
WAKE = "BASE,PING"          # wake-up message constantly sent
SLEEP = "BASE,GOTOSLEEP,"   # sleep message, sent on button press to deactivate the tag
ACK = "BASE,ACK"            # acknowledge receipt of message and tell tag to proceed

# RADIO
RADIO_FREQ_MHZ = 869.45
MAX_TX_POWER = 23

NO_COLLAR = -1              # ID to return if no collar is found
COLLAR_TIME_OUT = 120       # how long to wait before giving up on a collar

"""
Initialise the bluetooth device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
ble = BLERadio()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)


"""
Initialise the display
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
displayio.release_displays()

button_A = DigitalInOut(board.D9)
button_A.direction = Direction.INPUT
button_A.pull = Pull.UP

# Use for I2C
i2c = board.I2C()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)

display = adafruit_displayio_sh1107.SH1107(display_bus, width=WIDTH, height=HEIGHT)

# Make the display context
splash = displayio.Group(max_size=10)
display.show(splash)

color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000 # black # will try this orange colour #ff7400

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)

splash.append(bg_sprite)

text_area = label.Label(terminalio.FONT, text='Starting....', color=0xFFFFFF, x=8, y=8)
splash.append(text_area)

def screen_write(text=""):

    splash[1] = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=8, y=8)


"""
Initialise the LORA radio
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Define pins connected to the chip - this needs some wiring on the LoRa featherwing
# CS needs to be wired to B and RST needs to be wired to A and soldered in
CS = digitalio.DigitalInOut(board.D10)
RESET = digitalio.DigitalInOut(board.D11)

# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ, agc=True)
rfm9x = ulora.LoRa(spi, CS, modem_config=ulora.ModemConfig.Bw125Cr45Sf2048,tx_power=23)
"""
Send wake up message to gps tag
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
wake_msg = "GPS wake up"
stop_msg = "GpS stop"


# Set to max transmit power!
#rfm9x.tx_power = MAX_TX_POWER
#rfm9x.spreading_factor = 8
#rfm9x.signal_bandwidth = 250000#a62500
#rfm9x.coding_rate = 5

#print(rfm9x.bw_bins)

# send wake up message

packet = rfm9x.send(bytes("GPS wake up", "utf-8"),1)
print(packet)

screen_write("start GPS message send")
print("start GPS message send...")
time.sleep(3) # wait for two minutes

packet = rfm9x.receive()
print(packet)


while True:
    print("waiting for message...")
    screen_write("waiting for message...")
    packet = rfm9x.receive(timeout=20.0)
    # If no packet was received during the timeout then None is returned.
    if packet is not None:
        # Received a packet!
        # Print out the raw bytes of the packet:
        print("Received (raw bytes): {0}".format(packet))
        # And decode to ASCII text and print it too.  Note that you always
        # receive raw bytes and need to convert to a text format like ASCII
        # if you intend to do string processing on your data.  Make sure the
        # sending side is sending ASCII data before you try to decode!
        try:
            packet_text = str(packet, "ascii")
            print("Received (ASCII):\n {0}".format(packet_text))
            screen_write("Received (ASCII): {0}".format(packet_text))
        except:
            print("Message garbled")
            screen_write("Message garbled")
        # Also read the RSSI (signal strength) of the last received message and
        # print it.
        rssi = rfm9x.last_rssi
        print("Received signal \nstrength:\n {0} dB".format(rssi))
        screen_write("Received signal strength: {0} dB".format(rssi))
        rfm9x.send(bytes("And hello back to you\n", "utf-8"),1)
    else:
        print('no message')
        screen_write('no message')

    sleep(0.01)
