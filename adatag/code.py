# Author: Cyrus, Colin, Grant
# Date: Oct 2021
import gc

import adafruit_gps
import time
import board
import busio
from time import sleep
import digitalio

import adafruit_rfm9x

# Constant parameters
SLEEP_INTERVAL = 30*60  # time to sleep between checking for radio in seconds
NO_MSG_LIMIT = 5*60    # time without contact before returning to sleep
RADIO_FREQ_MHZ = 869.45 # Frequency of the radio in Mhz. 
COLLAR_ID = 1    # specify the collar ID - should be an integer less than 255 and greater than 0 (0 is the base station ID) 
BASE_ID = 0

# RADIO MESSAGES
WAKE = "B:PING"     # wake-up message constantly sent
SLEEP = "B:SLEEP"   # sleep message, sent on button press to deactivate the tag
SEND_GPS = "B:GPS"  # start sending gps  message, sent on button press to initiate gps broadcast

CS = digitalio.DigitalInOut(board.RFM9X_CS)
RESET = digitalio.DigitalInOut(board.RFM9X_RST)

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

while not spi.try_lock():
    spi.configure(baudrate=12000000)
spi.unlock()
# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# high power radios like the RFM95 can go up to 23 dB:
rfm9x.tx_power = 23
rfm9x.spreading_factor = 11
rfm9x.signal_bandwidth = 125000
rfm9x.coding_rate = 5

rfm9x.node = COLLAR_ID

uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=0.1,receiver_buffer_size=128)

# Create a GPS module instance.
gps = adafruit_gps.GPS(uart, debug=False)  # Use UART/pyserial


SLEEP_MODE=0
STANDBY_MODE=0
GPS_MODE=0

gps_send_interval=30


def initiate_sleep_mode():
    gps.send_command(b"PMTK161,0") #set GPS in to low power mode
    return



def initiate_standby_mode():
    # Turn on just minimum info (RMC only, location):
    gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
    # Set update rate to 60s fixes to get the gps ready 
    gps.send_command(b"PMTK220,60000")
    # send collar ID to base station
    print('sending awake message')
    rfm9x.send(bytes(str(COLLAR_ID) + ':AWAKE', "utf-8"),destination=BASE_ID)  

    return


def initiate_gps_mode():
    # Turn on just minimum info (RMC only, location):
    gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
    # Set gps update rate to 1s fixes 
    gps.send_command(b"PMTK220,1000")
    return

def one_step_sleep_mode():
    print('one step sleep')
    time.sleep(SLEEP_INTERVAL) 
    return

def one_step_standby_mode():
    print('one step standby')
    rfm9x.send(bytes(str(COLLAR_ID) + ':AWAKE', "utf-8"),destination=BASE_ID)  
    return 

def one_step_gps_mode():
    print('one step gps')
    start_send_time = time.monotonic()
    while True:
        sentence = gps._read_sentence()
        if sentence is not None:
            message = sentence[7:44] # use as small a packet as possible 
            rfm9x.send(bytes(message, "utf-8"),destination=BASE_ID)
        if time.monotonic() - start_send_time > gps_send_interval: 
            break
    return 


time_of_last_recv = time.monotonic()
time_of_last_send = time.monotonic()

receive_timeout = 20.0
# Main loop
while True:
    if time.monotonic() - time_of_last_recv > NO_MSG_LIMIT: 
        initiate_sleep_mode()
    print("checking for message...")
    packet = rfm9x.receive(timeout=receive_timeout) 
    if packet is not None:
        print("message received...")
        time_of_last_recv = time.monotonic()
        packet_text = str(packet, "ascii")
        if packet_text==SLEEP and not SLEEP_MODE:
            print("initiate sleep mode..")
            initiate_sleep_mode()
            STANDBY_MODE=GPS_MODE=0
            SLEEP_MODE=1
            receive_timeout = 20.0
        if packet_text==WAKE and not STANDBY_MODE:
            print("initiate standby mode..")
            initiate_standby_mode()
            time_of_last_send = time.monotonic()
            SLEEP_MODE=GPS_MODE=0
            STANDBY_MODE=1
            receive_timeout = 20.0
        if packet_text==SEND_GPS and not GPS_MODE:
            print("initiate gps mode..")
            initiate_gps_mode()
            SLEEP_MODE=STANDBY_MODE=0
            GPS_MODE=1
            receive_timeout = 2.0

    if SLEEP_MODE:
        one_step_sleep_mode()
        time_of_last_recv = time.monotonic()
    if STANDBY_MODE:
        one_step_standby_mode()
    if GPS_MODE:
        one_step_gps_mode()
    
    
