
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple GPS module demonstration.
# Will wait for a fix and print a message every second with the current location
# and other details.
import time
import board
import busio

from time import sleep

import adafruit_gps
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple demo of sending and recieving data with the RFM95 LoRa radio.
# Author: Tony DiCola
import digitalio

import adafruit_rfm9x


# Define radio parameters.
RADIO_FREQ_MHZ = 868.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Or uncomment and instead use these if using a Feather M0 RFM9x board and the appropriate
# CircuitPython build:
CS = digitalio.DigitalInOut(board.RFM9X_CS)
RESET = digitalio.DigitalInOut(board.RFM9X_RST)

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# Note that the radio is configured in LoRa mode so you can't control sync
# word, encryption, frequency deviation, or other settings!

# You can however adjust the transmit power (in dB).  The default is 13 dB but
# high power radios like the RFM95 can go up to 23 dB:
rfm9x.tx_power = 23


# Create a serial connection for the GPS connection using default speed and
# a slightly higher timeout (GPS modules typically update once a second).
# These are the defaults you should use for the GPS FeatherWing.
# For other boards set RX = GPS module TX, and TX = GPS module RX pins.
uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)

# for a computer, use the pyserial library for uart access
# import serial
# uart = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=10)

# If using I2C, we'll create an I2C interface to talk to using default pins
# i2c = board.I2C()

# Create a GPS module instance.
gps = adafruit_gps.GPS(uart, debug=False)  # Use UART/pyserial
# gps = adafruit_gps.GPS_GtopI2C(i2c, debug=False)  # Use I2C interface

# Initialize the GPS module by changing what data it sends and at what rate.
# These are NMEA extensions for PMTK_314_SET_NMEA_OUTPUT and
# PMTK_220_SET_NMEA_UPDATERATE but you can send anything from here to adjust
# the GPS module behavior:
#   https://cdn-shop.adafruit.com/datasheets/PMTK_A11.pdf

# Turn on the basic GGA and RMC info (what you typically want)
#gps.send_command(b"PMTK314,0,1,0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0")

#gps.send_command(b"PMTK314,1,1,1,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0")
# Turn on just minimum info (RMC only, location):
gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
# Turn off everything:
# gps.send_command(b'PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
# Turn on everything (not all of it is parsed!)
#gps.send_command(b'PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0')

# Set update rate to once a second (1hz) which is what you typically want.
gps.send_command(b"PMTK220,1000")
# Or decrease to once every two seconds by doubling the millisecond value.
# Be sure to also increase your UART timeout above!
# gps.send_command(b'PMTK220,2000')
# You can also speed up the rate, but don't go too fast or else you can lose
# data during parsing.  This would be twice a second (2hz, 500ms delay):
# gps.send_command(b'PMTK220,500')

# Main loop runs forever printing the location, etc. every second.
last_print = time.monotonic()
while True:
    sentence = gps._read_sentence()
    if sentence is None:
        continue
    #print(sentence)
    rfm9x.send(bytes(sentence + '\n', "utf-8"))
    #sleep(0.1)

#######################################################

# receive message to start and then start sending GPS, until receive stop message

# Author: Cyrus, Colin, Grant
# Date: 21 Oct 2021
# Simple GPS module demonstration.
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

# sleep funtion
def sleep_interval():
    time.sleep(10) # sleep duration can be changed

#name the collar ID
collar_ID = "Collar_ID WB100"

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# broadcast function
def Broadcast_mode():
    while True:
        # Turn on just minimum info (RMC only, location):
        gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Set update rate to once a second (1hz) which is what you typically want.
        gps.send_command(b"PMTK220,1000")

        # ~~~~~Main loop runs forever printing the location, etc. every second.
        last_print = time.monotonic()
        while True:
            f_print = time.monotonic()
            gps.update()
            sentence = gps._read_sentence()
            if sentence is None:
                continue
            ns = sentence.split(",")
            print(ns)
            if ns[2] == "A":
                f_print = time.monotonic()
                gps_stc=(ns[3]+ns[4] + "\n"+ ns[5]+ns[6])
                print(gps_stc)
                rfm9x.send(bytes(gps_stc + '\n', "utf-8"))
                #l_print = time.monotonic()
                #if l_print - last_print>120: #2 minutes
                    # print("break broadcast mode")
                    # receive a text
                    # if zzz break
                    #sleep(10)# sleep for some seconds
                    # break
                    # continue

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# standy_mode function
def standby_mode():
    while True:
        packet = rfm9x.send(bytes(collar_ID, "utf-8"))  # send via radio
        print("Hi, collar ID send")
        # sleep(1.0)
        #~ receive gps start message
        packet = rfm9x.receive(timeout=1.0)
        if packet is not None:
            packet_text = str(packet, "ascii")
            print("Received (ASCII):\n {0}".format(packet_text))
            # print(packet)
            if packet_text == "AAA":
                print("GPS intiated")
                message = "broadcast mode intiated"
                packet = rfm9x.send(bytes(message, "utf-8"))  # send via radio
                Broadcast_mode() # activate broadcast
# Main loop
while True:
    packet = rfm9x.send(bytes("GPS tag available", "utf-8"))  # tag announces its presence
    print("Hi,\nA gps tag is available")

    packet = rfm9x.receive(timeout=2.0)  #check message listen for incoming message for 5 minutes
    if packet is not None:
        print("Received (ASCII):\n {0}".format(packet))
        standby_mode()  # this is a function
    else:
        sleep_interval()















