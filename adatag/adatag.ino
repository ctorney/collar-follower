
/*
# Copyright 2022 Colin Torney
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
*/


#include <SPI.h>
#include <LoRa.h>



#include <SAMDTimerInterrupt.h>
#include <SAMD_ISR_Timer.h>
#include <Adafruit_GPS.h>

#define GPSSerial Serial1

#define GPS_INTERRUPT_MS        10     // 1s = 1000ms
#define NMEA_SENTENCE_MAX_LEN   82     


#define DIO0 3
#define SS   8
#define RESET 4

#define RF95_FREQ 868.0

#define SLEEP_MODE  0x01   // sleep
#define STDBY_MODE  0x02   // standing by
#define BCGPS_MODE  0x03   // broadcast GPS

// RADIO MESSAGES
#define WAKE "B:PING"     // wake-up message constantly sent
#define SLEEP "B:SLEEP"   // sleep message, sent on button press to deactivate the tag
#define SEND_GPS "B:GPS"  // start sending gps  message, sent on button press to initiate gps broadcast

#define RESPONSE "AWAKE\n"     // response to wake-up message

volatile byte mode = 0x00;
volatile byte mode_change = 0;

volatile unsigned long time_of_last_message;  //some global variables available anywhere in the program

const unsigned long SLEEP_INTERVAL = 30*60*1000;  //// time to sleep between checking for radio in milliseconds
const unsigned long NO_MSG_LIMIT = 5*60*1000;    // time without contact before returning to sleep


int longRangeSpreadingFactor = 11;
int shortRangeSpreadingFactor = 7;
long signalBandwidth = 125E3;
int codingRateDenominator = 5;


Adafruit_GPS GPS(&GPSSerial);


uint32_t timer = millis();



byte msgflag = 0;         // unused message flag
byte collar_id = 0x01;    // address of this device
byte base_id = 0x00;      // destination to send to
byte broadcast = 0xFF;    // broadcasting address


// interrupt to read GPS 
void gps_interrupt(void) {if (mode!=SLEEP_MODE) GPS.read();}

void setup()
{
  Serial.begin(115200);
  // while (!Serial);

  Serial.println("Adafruit GPS collar and LoRa broadcaster.");

  // create the GPS interrupt
  SAMDTimer ITimer0(TIMER_TC3);  
  ITimer0.attachInterruptInterval(GPS_INTERRUPT_MS * 1000, gps_interrupt);    // interval in microsecs
    

  // initialise GPS 
  GPS.begin(9600);
  GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCONLY);
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ);     // 0.1 Hz update rate on startup
  GPS.sendCommand(PMTK_API_SET_FIX_CTL_100_MILLIHERTZ);     // 0.1 Hz update rate on startup
  
  delay(1000);


  // setup LoRa
  LoRa.setPins(SS, RESET, DIO0);
  
  if (!LoRa.begin(868E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
  LoRa.setSpreadingFactor(longRangeSpreadingFactor);
  LoRa.setSignalBandwidth(signalBandwidth);
  LoRa.setCodingRate4(codingRateDenominator);
  LoRa.setTxPower(20);
  LoRa.enableCrc();
  
  LoRa.onReceive(onReceive);                                // register the receive callback
  delay(1000);

  time_of_last_message = millis();

}


void loop() 
{
  
  delay(10);

  // sleep if no message has been received for a while
  unsigned long currentMillis = millis();  
  if (currentMillis - time_of_last_message >= NO_MSG_LIMIT)  
  {
    mode=SLEEP_MODE;
    mode_change=1;
  }

  // preparation steps if the mode has changed
  if (mode_change) mode_update();

  switch (mode)
  {
    case SLEEP_MODE:
      one_step_sleep_mode();
      break;
    case STDBY_MODE:
      one_step_standby_mode();
      break;
    case BCGPS_MODE:
      one_step_gps_mode();
      break;

    
  }
  LoRa.receive();

  
}

void one_step_gps_mode()
{

  // check for GPS sentence and broadcast to base station
  if (GPS.newNMEAreceived()) 
  {

    String sentence = "";                 
    char *nmea = GPS.lastNMEA();

    for (int i = 0; i < NMEA_SENTENCE_MAX_LEN; i++) 
    {
          char curr_char = nmea[i];
          sentence += curr_char;
          if (curr_char == '\n') break;
    }
    //Serial.println(sentence);

    sendMessage(sentence);

  }

  // reenter receive mode
  LoRa.receive();

}

void one_step_standby_mode()
{
  //Serial.println("one step standby");
  // check for GPS sentence and broadcast to base station
  if (GPS.newNMEAreceived()) 
  {

    String sentence = "";                 
    char *nmea = GPS.lastNMEA();

    for (int i = 0; i < NMEA_SENTENCE_MAX_LEN; i++) 
    {
          char curr_char = nmea[i];
          sentence += curr_char;
          if (curr_char == '\n') break;
    }
    //Serial.println(sentence);

    sendMessage(sentence);

  
    
  }
  else
    sendMessage(RESPONSE);
  

  LoRa.receive();
  delay(2000);
}


void one_step_sleep_mode()
{ 
  mode = 0x00;
  LoRa.sleep();
  GPS.standby();// set GPS in to low power mode;
  delay(SLEEP_INTERVAL);
  LoRa.idle();
  LoRa.setSpreadingFactor(longRangeSpreadingFactor);
  time_of_last_message = millis();

}


void mode_update()
{
  switch (mode)
  { 
    case SLEEP_MODE:      
      //Serial.println("having a sleep");
      break;
    case STDBY_MODE:
      GPS.wakeup();// wake GPS
      // Set gps update rate to 10s fixes to get ready
      GPS.sendCommand(PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ);     // 0.1 Hz update rate 
      GPS.sendCommand(PMTK_API_SET_FIX_CTL_100_MILLIHERTZ);     // 0.1 Hz update rate 
      //Serial.println("entering standby");
      break;
    case BCGPS_MODE:
      GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ);     // Set gps update rate to 1s fixes 
      GPS.sendCommand(PMTK_API_SET_FIX_CTL_1HZ);     // Set gps update rate to 1s fixes 
      //Serial.println("entering gps mode");
      break;
  }
  mode_change=0;
}


void sendMessage(String outgoing) 
{
  while (LoRa.beginPacket() == 0) {
    //Serial.print("waiting for radio ... ");
    delay(100);
  }
  LoRa.beginPacket();                   // start packet
  LoRa.write(base_id);                  // add destination address
  LoRa.write(collar_id);                // add sender address
  LoRa.write(msgflag);                  // add message ID
  LoRa.write(outgoing.length());        // add payload length
  LoRa.print(outgoing);                 // add payload
  LoRa.endPacket();                     // finish packet and send it
}





void onReceive(int packetSize) {
  if (packetSize == 0) return;          // if there's no packet, return

  // read packet header bytes:
  int recipient = LoRa.read();          // recipient address
  byte sender = LoRa.read();            // sender address
  byte incomingMsgId = LoRa.read();     // incoming msg ID
  byte incomingLength = LoRa.read();    // incoming msg length

  String incoming = "";                 // payload of packet

  while (LoRa.available()) {            // can't use readString() in callback, so
    incoming += (char)LoRa.read();      // add bytes one by one
  }

  // if message is for this device, or broadcast, print details:
  //Serial.println("Received from: 0x" + String(sender, HEX));
  //Serial.println("Sent to: 0x" + String(recipient, HEX));
  //Serial.println("Message ID: " + String(incomingMsgId));
  //Serial.println("Message length: " + String(incomingLength));
  //Serial.println("Message: " + incoming);
  //Serial.println("RSSI: " + String(LoRa.packetRssi()));
  //Serial.println("Snr: " + String(LoRa.packetSnr()));
  //Serial.println();
  
  // if the recipient isn't this device or broadcast,
  if (recipient != collar_id && recipient != broadcast) {
    Serial.println("This message is not for me.");
    return;                             // skip rest of function
  }

  // the base station has connected with us so switch to fast short-range comms
  if (recipient == collar_id) 
    LoRa.setSpreadingFactor(shortRangeSpreadingFactor);
    
  time_of_last_message = millis();

  if ((incoming==SLEEP)&&(mode!=SLEEP_MODE))
  {
    mode=SLEEP_MODE;
    mode_change=1;
  }

  if ((incoming==WAKE)&&(mode!=STDBY_MODE))
  {
    mode=STDBY_MODE;
    mode_change=1;
  }

  if ((incoming==SEND_GPS)&&(mode!=BCGPS_MODE))
  {
    mode=BCGPS_MODE;
    mode_change=1;
  }

  

}
