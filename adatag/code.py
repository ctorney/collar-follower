# receive message to start and then start sending GPS, until receive stop message

# Author: Cyrus, Colin, Grant
# Date: Oct 2021
# Will wait for a fix and print a message every second with the current location
# and other details.
import time
import board
import busio

from time import sleep

import adafruit_gps
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import digitalio
import adafruit_rfm9x
# Define radio parameters.
RADIO_FREQ_MHZ = 869.45  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 869.45, etc.

# Or uncomment and instead use these if using a Feather M0 RFM9x board and the appropriate
# CircuitPython build:
CS = digitalio.DigitalInOut(board.RFM9X_CS)
RESET = digitalio.DigitalInOut(board.RFM9X_RST)

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

rfm9x.tx_power = 23
# For other boards set RX = GPS module TX, and TX = GPS module RX pins.
uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)

# Create a GPS module instance.
gps = adafruit_gps.GPS(uart, debug=False)  # Use UART/pyserial


sleep_interval=30*60 # 30 minutes
# sleep funtion
def sleep_mode():
    set_low_powermode()
    time.sleep(sleep_interval) # sleep duration can be changed
    return 

#name the collar ID
collar_ID = "Collar_ID WB100"
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# low power mode funtion
def set_low_powermode():
    gps.send_command(b"PMTK161,0")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# broadcast function
def broadcast_mode():
    

    # Set update rate to once a second (1hz) which is what you typically want.
    gps.send_command(b"PMTK220,1000")

    # ~~~~~Main loop runs forever printing the location, etc. every second.
    time_of_last_msg = time.monotonic()
    time_of_last_check = time.monotonic()
    
    CHECK_INTERVAL = 5
    NO_MSG_LIMIT = 10*60
    
    while True:
        # gps.update()
        sentence = gps._read_sentence()
        if sentence is None:
            continue
        rfm9x.send(bytes(sentence + '\n', "utf-8"))
        
        
        if time.monotonic() - time_of_last_check > CHECK_INTERVAL: # check the radio for base station messages
            packet = rfm9x.receive(timeout=0.5)
            time_of_last_check = time.monotonic()
            if packet is not None:
                time_of_last_msg = time.monotonic()
                try:
                    packet_text = str(packet, "ascii")
                
                    if packet_text=="ZZZ":
                        return
                except:
                    pass
        
        if time.monotonic() - time_of_last_msg > NO_MSG_LIMIT: # check the radio for base station messages
              return  
            
        
        

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# standy_mode function
def standby_mode():
    
    # Turn on just minimum info (RMC only, location):
    gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
    
    # Set update rate to once a second (30s fixes) which is what you typically want.
    gps.send_command(b"PMTK220,30000")
    
    
    time_of_last_msg = time.monotonic()
    NO_MSG_LIMIT = 10*60

    rfm9x.send(bytes(collar_ID, "utf-8"))  # send via radio
    
    while True:
        packet = rfm9x.receive(timeout=5.0)
        if packet is not None:
            time_of_last_msg = time.monotonic()
            try: 
                packet_text = str(packet, "ascii")
                print("Received (ASCII):\n {0}".format(packet_text))
                # print(packet)
                if packet_text == "AAA":
                    print("GPS intiated")
                    message = "broadcast mode\ninitiated"
                    rfm9x.send(bytes(message, "utf-8"))  # send via radio
                    broadcast_mode() # activate broadcast
                    return
                if packet_text == "ZZZ":
                    rfm9x.send(bytes("low power\nmode activated", "utf-8"))
                    return
            except:
                pass
        if time.monotonic() - time_of_last_msg > NO_MSG_LIMIT: # check the radio for base station messages
            print("standby mode deactivated")
            return  




LISTEN_TIME = 60*5

# Main loop
while True:
   
    start_listen_time = time.monotonic()
    while True:
        packet = rfm9x.receive(timeout=1.0)  #check message listen for incoming message for 5 minutes
        if packet is not None:
            print("Received (ASCII):\n {0}".format(packet))
            standby_mode()
            break
        if time.monotonic()-start_listen_time > LISTEN_TIME:
            break
    
    print("has entered sleep interval")
    sleep_mode()
    
