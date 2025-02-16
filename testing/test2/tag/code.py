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

# Simple demo of sending and recieving data with the RFM95 LoRa radio.
# Author: Tony DiCola
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


#name the collar ID
collar_ID = "Collar_ID WB100"
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
            # print(packet)
            # Turn on just minimum info (RMC only, location):
            gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
            # Set update rate to once a second (1hz) which is what you typically want.
            gps.send_command(b"PMTK220,1000")

            # ~~~~~Main loop runs forever printing the location, etc. every second.
            last_print = time.monotonic()
            while True:
                gps.update()
                sentence = gps._read_sentence()
                if sentence is None:
                    continue
                ns = sentence.split(",")
                if ns[2] == "A":
                    gps_stc=(ns[3]+ns[4] + "\n"+ ns[5]+ns[6])
                    print(gps_stc)
                    rfm9x.send(bytes(gps_stc + '\n', "utf-8"))
        #sleep(0.1)


