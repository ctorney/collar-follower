
# Copyright 2021 Colin Torney
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This code is for the collar-follower base station. It is based on adafruit code
and will send messages to a GPS tag to turn on high frequency fix mode then 
forward fixes over bluetooth to an android tablet. 
"""

import board
import busio
import displayio
import terminalio
from time import sleep

from adafruit_display_text import label
import adafruit_displayio_sh1107
from digitalio import DigitalInOut, Direction, Pull
import digitalio

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.button_packet import ButtonPacket

import adafruit_rfm9x

"""
Constant parameters
"""
# LED DISPLAY
WIDTH = 128
HEIGHT = 64
BORDER = 2

# RADIO MESSAGES
WAKE = "BASE,PING"          # wake-up message constantly sent
SLEEP = "BASE,GOTOSLEEP,"   # sleep message, sent on button press to deactivate the tag
ACK = "BASE,ACK"            # acknowledge receipt of message and tell tag to proceed

# RADIO
RADIO_FREQ_MHZ = 868.0
MAX_TX_POWER = 23

NO_COLLAR = -1              # ID to return if no collar is found
COLLAR_TIME_OUT = 10        # how long to wait before giving up on a collar

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
color_palette[0] = 0x000000 # black 

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
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# Set to max transmit power!
rfm9x.tx_power = MAX_TX_POWER



"""
Send a wakeup message to any tags in the vicinity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def send_wakeup():
    collar_id = NO_COLLAR

    # send a broadcast mesage
    rfm9x.send(bytes(WAKE, "UTF-8"))

    # Look for a new packet - wait up to 5 seconds:
    packet = rfm9x.receive(timeout=5.0)
    if packet is not None:
        txtpacket = packet.decode()
        txtpacket = txtpacket.split(",")
        if txtpacket[1]=="AWAKE":
            collar_id = int(txtpacket[0])
    return collar_id



"""
Send a sleep message to the active tag
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def send_sleep(collar_id):
    # send a sleep message 5 times
    screen_write("Sending collar\nid:" + str(collar_id) + " back\nto sleep.")
    for i in range(5):
        rfm9x.send(bytes(SLEEP+str(collar_id), "UTF-8"))
        sleep(1)




"""
Forward all messages received from the tag to the connected bluetooth device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def forward_mode(collar_id):
    screen_write("Connected to\ncollar id:\n" + str(collar_id) + ". Press and hold A\nto disconnect")

    timeout_count = 0
    while True:
        timeout_count+=1
        packet = rfm9x.receive(timeout=1.0)
        if packet is not None:
            txtpacket = packet.decode()
            txtpacket = txtpacket.split(",")
            if collar_id == int(txtpacket[0]):
                timeout_count = 0
                try:
                    uart.write(packet)
                except:
                    # any errors with the bluetooth we'll exit and try and reconnect
                    break
                rfm9x.send(bytes(ACK, "UTF-8"))
        if timeout_count>COLLAR_TIME_OUT:
            send_sleep(collar_id)
            break
        if not button_A.value:
            send_sleep(collar_id)
            break





"""
Main loop: 
1. Connects to bluetooth device
2. Broadcasts a wake-up message every 5 seconds
3. If a tag responds it enters a message forwarding mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
while True:
    screen_write("Advertising\nBLE device:\n" + ble.name)
    ble.start_advertising(advertisement)
    while not ble.connected:
        pass

    screen_write("Bluetooth\nconnected.\nScanning...")
    # Now we're connected
    while ble.connected:
        collar_id = send_wakeup()

        if collar_id!=NO_COLLAR:
            forward_mode(collar_id)
        
        # wait 5 seconds before trying again
        sleep(5) 

