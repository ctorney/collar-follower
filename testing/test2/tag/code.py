# receive message to start and then start sending GPS, until receive stop message


# Simple GPS module demonstration Will wait for a fix and print a message every second with the current location and other details.
import time
import board
import busio

from time import sleep

import adafruit_gps
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
collar_ID = "the collar_ID is WB100"
packet = rfm9x.send(bytes(collar_ID + '\n', "utf-8"))  # send via radio
print(packet)
print("collar_id send")

# receive wake up message
packet = rfm9x.receive()
print(packet)
# sleep(3)
if packet is not None:
    try:
        txtpacket = packet.decode()
        textpacket = txtpacket.split(",")
        if txtpacket[1]== Wake:
            message = "broadcast mode intiated"
            packet = rfm9x.send(bytes(message, "utf-8"))  # send via radio
            print(packet)
            # Turn on just minimum info (RMC only, location):
            gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
            # Set update rate to once a second (1hz) which is what you typically want.
            gps.send_command(b"PMTK220,5000")

            # ~~~~~Main loop runs forever printing the location, etc. every second.
            last_print = time.monotonic()
            while True:
                sentence = gps._read_sentence()
                if sentence is None:
                    continue
                print(sentence)
                rfm9x.send(bytes(sentence + '\n', "utf-8"))
                # sleep(0.1)
        elif packet == "GPS stop":
            print("GPS has stopped")
            gps.send_command(b"PMTK161,0") # GPS enters into low power mode
            packet = rfm9x.send(bytes("GPS low power mode initiated", "utf-8"))
            print("GPS low power mode initiated")
    except:
        pass

