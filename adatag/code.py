# Author: Cyrus, Colin, Grant
# Date: Oct 2021
import time
import board
import busio
from time import sleep
import adafruit_gps
import digitalio
import ulora


# Constant parameters
SLEEP_INTERVAL = 30*60  # time to sleep between checking for radio in seconds
LISTEN_TIME = 60*5      # time to listen for a wake up message
NO_MSG_LIMIT = 10*60    # time without contact before returning to sleep
RADIO_FREQ_MHZ = 869.45 # Frequency of the radio in Mhz. 
COLLAR_ID = "1"    # name the collar ID
# RADIO MESSAGES
WAKE = "BASE,PING"          # wake-up message constantly sent
SLEEP = "BASE,GOTOSLEEP"    # sleep message, sent on button press to deactivate the tag
BCAST = "BASE,START,"        # start message, sent on button press to initiate gps broadcast
START = "COLLAR,STARTING"   # start message, sent on button press to initiate gps broadcast
ACK = "BASE,ACK"            # acknowledge receipt of message and tell tag to proceed

CS = digitalio.DigitalInOut(board.RFM9X_CS)
RESET = digitalio.DigitalInOut(board.RFM9X_RST)

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialze RFM radio
rfm9x = ulora.LoRa(spi, CS, modem_config=ulora.ModemConfig.Bw125Cr45Sf2048,tx_power=23,freq=RADIO_FREQ_MHZ) 

uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)

# Create a GPS module instance.
gps = adafruit_gps.GPS(uart, debug=False)  # Use UART/pyserial

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# sleep mode
# - check that gps is in low power mode
# - wait for fixed amount of time before checking the radio again
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def sleep_mode():
    gps.send_command(b"PMTK161,0") #set GPS in to low power mode
    time.sleep(SLEEP_INTERVAL) 
    return 

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# standby mode function
# - base station is in the area so start gps
# - check for wake up message
# - back to sleep if no wake up after fixed time interval
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def standby_mode():
    
    # Turn on just minimum info (RMC only, location):
    gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
    # Set update rate to 60s fixes to get the gps ready 
    gps.send_command(b"PMTK220,60000")
    
    time_of_last_msg = time.monotonic()
    
    while True:
        # send collar ID to base station
        rfm9x.send(bytes(COLLAR_ID + ',AWAKE', "utf-8"),0)  
        print("Standby mode: listening for message")
        packet = rfm9x.receive(timeout=5.0)
        if packet is not None:
            time_of_last_msg = time.monotonic()
            try: 
                packet_text = str(packet, "ascii")
                print("Received (ASCII):\n {0}".format(packet_text))
                # print(packet)
                if packet_text == BCAST + COLLAR_ID:
                    print("GPS intiated")
                    message = "broadcast mode\ninitiated"
                    rfm9x.send(bytes(message, "utf-8"),0)  # send via radio
                    # activate broadcast 
                    broadcast_mode() 
                    return
                if packet_text == SLEEP:
                    rfm9x.send(bytes("low power\nmode activated", "utf-8"))
                    return
            except:
                pass
        if time.monotonic() - time_of_last_msg > NO_MSG_LIMIT: 
            print("standby mode terminated")
            return  


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# broadcast function
def broadcast_mode():
    
    # Set update rate to once a second (1hz) which is what you typically want.
    gps.send_command(b"PMTK220,1000")

    # ~~~~~Main loop runs forever printing the location, etc. every second.
    time_of_last_msg = time.monotonic()
    time_of_last_check = time.monotonic()
    
    CHECK_INTERVAL = 5
    
    while True:
        # gps.update()
        sentence = gps._read_sentence()
        if sentence is None:
            continue
        rfm9x.send(bytes(sentence + '\n', "utf-8"))
          
        if time.monotonic() - time_of_last_check > CHECK_INTERVAL: # check incoming messages and execute the relevant command 
            packet = rfm9x.receive(timeout=0.5)
            time_of_last_check = time.monotonic()
            if packet is not None:
                time_of_last_msg = time.monotonic()
                try:
                    packet_text = str(packet, "ascii")
                    if packet_text==SLEEP: #exit broadcast mode and return to standby mode
                        return
                except:
                    pass
        
        if time.monotonic() - time_of_last_msg > NO_MSG_LIMIT: #exit broadcast mode and return to standby mode
            return  
            

# Main loop
while True:
    start_listen_time = time.monotonic()
    print("listening...")
    while True:
        # Listen for incoming message for 5 minutes duration
        packet = rfm9x.receive(timeout=1.0) 
        if packet is not None:
            print("Received (ASCII):\n {0}".format(packet))
            standby_mode()
            break
        else:
            print("no message received")
        if time.monotonic()-start_listen_time > LISTEN_TIME:
            break
        time.sleep(2.0) 
    
    print("has entered sleep interval")
    # enter sleep mode
    sleep_mode()
    
