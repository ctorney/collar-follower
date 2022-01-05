
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
import time

from adafruit_display_text import label
import adafruit_displayio_sh1107
from digitalio import DigitalInOut, Direction, Pull
import digitalio

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from adafruit_bluefruit_connect.packet import Packet

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
WAKE = "B:PING"          # wake-up message constantly sent
SLEEP = "B:SLEEP"    # sleep message, sent on button press to deactivate the tag
SEND_GPS = "B:GPS"        # start sending gps  message, sent on button press to initiate gps broadcast
MAX_MSG = 30                # how many times to send an instruction before giving up


# RADIO
RADIO_FREQ_MHZ = 869.45
MAX_TX_POWER = 23

BASE_ID = 0
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

button_B = DigitalInOut(board.D6)
button_B.direction = Direction.INPUT
button_B.pull = Pull.UP

button_C = DigitalInOut(board.D5)
button_C.direction = Direction.INPUT
button_C.pull = Pull.UP

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

while not spi.try_lock():
    spi.configure(baudrate=12000000)
spi.unlock()

# Define pins connected to the chip - this needs some wiring on the LoRa featherwing
# CS needs to be wired to B and RST needs to be wired to A and soldered in 
CS = digitalio.DigitalInOut(board.D10)
RESET = digitalio.DigitalInOut(board.D11)


# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# high power radios like the RFM95 can go up to 23 dB:
rfm9x.tx_power = 23
rfm9x.spreading_factor = 11
rfm9x.signal_bandwidth = 125000
rfm9x.coding_rate = 5

rfm9x.node = BASE_ID
"""
Send a wakeup message to any tags in the vicinity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def send_wakeup():
    collar_id = NO_COLLAR

    if DEBUG: 
        print("sending wake up message", WAKE)
    # send a broadcast mesage
    rfm9x.send(bytes(WAKE, "UTF-8"))

    # Look for a new packet - wait up to 1 seconds:
    packet = rfm9x.receive(timeout=10.0)
    if packet is not None:
        try:
            txtpacket = str(packet, "UTF-8")

            print('received', txtpacket)
            txtpacket = txtpacket.split(":")
            if txtpacket[1]=="AWAKE":
                collar_id = int(txtpacket[0])
                print(collar_id)
        except:
            pass
    return collar_id



"""
Send a sleep message to the active tag
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def send_sleep(collar_id):
    # send a sleep message MAX_MSG times
    screen_write("Sending collar\nid:" + str(collar_id) + " back\nto sleep.")
    for i in range(MAX_MSG):
        rfm9x.send(bytes(SLEEP, "UTF-8"),destination=collar_id)
        #packet = rfm9x.receive(timeout=1.0)             # check if there's a message
        #if packet is not None:
        #    try:
        #        txtpacket = str(packet, "ascii")
        #        print(txtpacket)
        #        if txtpacket == SLEEPING:
        #            screen_write("Collar " + str(collar_id) + " sleeping")
        #            sleep(2)
        #            break
        #    except:
        #        # any errors in the decoding we'll just continue
        #        pass

        sleep(2)


"""
Forward all messages received from the tag to the connected bluetooth device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def forward_mode(collar_id):

    time_of_last_msg = time.monotonic()
    time_refresh = 0
    while True:
        rfm9x.send(bytes(SEND_GPS, "UTF-8"),destination=collar_id)             # send GPS instruction
        if time.monotonic() - time_refresh > screen_refresh:
            time_since_msg = time.monotonic() - time_of_last_msg 
            screen_write("C" + str(collar_id) + " MODE: GPS\nHold B to standby\nRS:" + str(rfm9x.last_rssi) + " LMT:" + str(time_since_msg))
            time_refresh = time.monotonic()

        packet = rfm9x.receive(timeout=10.0)             # check if there's a message
        #rfm9x.send(bytes(SEND_GPS, "UTF-8"),destination=collar_id)             # send GPS instruction
        if packet is not None:
            time_of_last_msg = time.monotonic()
            if ble.connected: 
                uart.write(packet)
            if DEBUG:
                try:
                    packet_text = str(packet, "UTF-8")
                    print('RECV PACKET:', packet_text)
                except:
                    # any errors in the decoding we'll just continue
                    pass

        if not button_B.value:
            break
        if not ble.connected and not ble.advertising: 
                #ble.stop_advertising()
            #uart = UARTService()
            #advertisement = ProvideServicesAdvertisement(uart)
            ble.start_advertising(advertisement)

"""
Standby mode - keep collar awake but send wake up or sleep messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def standby_mode(collar_id):

    standby_send_interval = 10.0
    time_of_last_msg = time.monotonic()
    time_of_last_send = time.monotonic()
    time_refresh = 0
    while True:
        if time.monotonic() - time_of_last_send > standby_send_interval:
            rfm9x.send(bytes(WAKE, "UTF-8"),destination=collar_id)             # send GPS instruction

            packet = rfm9x.receive(timeout=10.0)             # check if there's a message
            rfm9x.send(bytes(WAKE, "UTF-8"),destination=collar_id)             # send GPS instruction
            if packet is not None:

                time_of_last_msg = time.monotonic()
                try:
                    packet_text = packet.decode()#str(packet, "ascii")
                    print('RECV PACKET:', packet_text)
                except:
                    # any errors in the decoding we'll just continue
                    pass
            time_of_last_send = time.monotonic()

        if time.monotonic() - time_refresh > screen_refresh:
            time_since_msg = time.monotonic() - time_of_last_msg 
            screen_write("C" + str(collar_id) + " MODE: STANDBY\nHold A to start gps\nHold C to send sleep\nRS:" + str(rfm9x.last_rssi) + " LMT:" + str(time_since_msg))
            time_refresh = time.monotonic()
        
        if not button_A.value:
            forward_mode(collar_id)
        if not button_C.value:
            break
        if not ble.connected and not ble.advertising: 
                #ble.stop_advertising()
            #uart = UARTService()
            #advertisement = ProvideServicesAdvertisement(uart)
            ble.start_advertising(advertisement)

    send_sleep(collar_id)


"""
Connect option - option to connect based on collar ID or ignore
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
def connect_option(collar_id):


    screen_write("Connect to collar " + str(collar_id) + "?\nHold B to connect\nHold C to ignore")
    time_now = time.monotonic()
    timeout = 300  # expect after 5 minutes collar will be back asleep
    while True:
        if time.monotonic() - time_now > timeout:
            break
        if not button_B.value:
            standby_mode(collar_id)
            break
        if not button_C.value:
            break




"""
Main loop: 
1. Connects to bluetooth device
2. Broadcasts a wake-up message every 5 seconds
3. If a tag responds it enters a message forwarding mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
while True:
    screen_write("BLE device:\n" + ble.name + "\nConnect or press\nA to continue" )
    ble.start_advertising(advertisement)
    while not ble.connected:
        if not button_A.value:
            break
    ble.stop_advertising()


    time_now = time.monotonic()
    screen_write("Bluetooth connected.\nBroadcasting\nwake up message...")
    # Now we're connected
    while ble.connected or DEBUG:
        # send wake-up
        collar_id = send_wakeup()

        print('wakeup returned collar id', str(collar_id))
        
        # enter msg forwarding if we've found a collar or we're in debug mode
        if collar_id!=NO_COLLAR:
            connect_option(collar_id)

        # wait 1 seconds between wake up messages
        sleep(1) 

        if time.monotonic() - time_now > screen_refresh:
            screen_write("Broadcasting\nwake up message...")
            time_now = time.monotonic()
        

