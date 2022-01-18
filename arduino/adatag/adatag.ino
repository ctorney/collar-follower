

#include <SAMDTimerInterrupt.h>
#include <SAMD_ISR_Timer.h>

 
#include <RHReliableDatagram.h>
#include <RH_RF95.h>
#include <SPI.h>

#define GPS_INTERRUPT_MS        10     // 1s = 1000ms
#define NMEA_SENTENCE_MAX_LEN   82     



 // for feather m0  
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 3


#define RF95_FREQ 868.0


#define CLIENT_ADDRESS 1
#define SERVER_ADDRESS 2
 



#include <Adafruit_GPS.h>

// what's the name of the hardware serial port?
#define GPSSerial Serial1

// Connect to the GPS on the hardware port
Adafruit_GPS GPS(&GPSSerial);

// Set GPSECHO to 'false' to turn off echoing the GPS data to the Serial console
// Set to 'true' if you want to debug and listen to the raw GPS sentences
#define GPSECHO false

uint32_t timer = millis();


// Radio driver and manager
RH_RF95 driver(RFM95_CS, RFM95_INT);
RHReliableDatagram manager(driver, CLIENT_ADDRESS);



void gps_interrupt(void)
{
    GPS.read();
}

void setup()
{
  return;
  Serial.begin(115200);
  Serial.println("Adafruit GPS library basic parsing test!");
  // Init timer ITimer1
  SAMDTimer ITimer0(TIMER_TC3);  
  // Interval in microsecs
  if (ITimer0.attachInterruptInterval(GPS_INTERRUPT_MS * 1000, gps_interrupt))
    Serial.println("Starting  ITimer0 OK, millis() = " + String(millis()));
  else
    Serial.println("Can't set ITimer0. Select another freq. or timer");
  

  // GPS initialise
  GPS.begin(9600);

  GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCONLY);
  //GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ); // 1 Hz update rate
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ); // 1 Hz update rate
  
  delay(1000);

  if (!manager.init())
    Serial.println("init failed");
  
  if (!driver.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  
  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);

  // LoRa settings
  driver.setModemConfig(RH_RF95::Bw125Cr45Sf128);
  driver.setTxPower(23, false);
  manager.setRetries(0);
  delay(1000);
  
}

uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];

void loop() // run over and over again
{
    return;

  if (GPS.newNMEAreceived()) {
    Serial.print(GPS.lastNMEA()); // this also sets the newNMEAreceived() flag to false
    
    if (manager.sendtoWait((uint8_t *)GPS.lastNMEA(), NMEA_SENTENCE_MAX_LEN, SERVER_ADDRESS))
    {
          Serial.println("sendtoWait succeeded");
      
// Now wait for a reply from the server
    uint8_t len = sizeof(buf);
    uint8_t from;   
    if (manager.recvfromAckTimeout(buf, &len, 900, &from))
    {
      Serial.print("got reply from : 0x");
      Serial.print(from, HEX);
      Serial.print(": ");
      Serial.println((char*)buf);
  
  
    }
          
    }
    else
      Serial.println("sendtoWait failed");
  }
    

  
}

/*

#include <Adafruit_PMTK.h>
#include <Adafruit_GPS.h>
#include <NMEA_data.h>

 
#include <RHReliableDatagram.h>
#include <RH_RF95.h>
#include <SPI.h>


 // for feather m0  
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 3


#define RF95_FREQ 868.0


#define CLIENT_ADDRESS 1
#define SERVER_ADDRESS 2
 

// Radio driver and manager
RH_RF95 driver(RFM95_CS, RFM95_INT);
RHReliableDatagram manager(driver, CLIENT_ADDRESS);
 
 
void setup() 
{
  Serial.begin(9600);
  while (!Serial) ; // Wait for serial port to be available
  if (!manager.init())
    Serial.println("init failed");
  
  if (!driver.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  
  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);

  // LoRa settings
  driver.setModemConfig(RH_RF95::Bw125Cr45Sf128);
  driver.setTxPower(23, false);
  manager.setRetries(0);
}
 
uint8_t data[] = "Hello World!";
// Dont put this on the stack:
uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
 
void loop()
{
  Serial.println("Sending to rf95_reliable_datagram_server");

  if (manager.waitAvailableTimeout(200))
  {


    // Now wait for a reply from the server
    uint8_t len = sizeof(buf);
    uint8_t from;   
    
    if (manager.recvfrom(buf, &len, &from))
    {
      Serial.print("got reply : 0x");
      Serial.print(from, HEX);
      Serial.print(": ");
      Serial.println((char*)buf);
      Serial.print( manager.retries(),HEX);
    }
    else
    {
      Serial.println("No reply, is rf95_reliable_datagram_server running?");
    }

    
  }
  else
  {
    // Send a message to manager_server
    if (manager.sendto(data, sizeof(data), SERVER_ADDRESS))
    {
      manager.waitPacketSent();
    Serial.println("sendtoWait succeeded");
    }
    else
      Serial.println("sendtoWait failed");
  }
  //
  // delay(500);
}
 



/*
#include <RHDatagram.h>


#include <SPI.h>
#include <RH_RF95.h>

// for feather m0  
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 3


#define CLIENT_ADDRESS 1
#define SERVER_ADDRESS 2


// Change to 434.0 or other frequency, must match RX's freq!
#define RF95_FREQ 868.0

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);


// Class to manage message delivery and receipt, using the driver declared above
RHDatagram manager(rf95, CLIENT_ADDRESS);


void setup() 
{
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  Serial.begin(115200);

  delay(100);

  Serial.println("Feather LoRa TX Test!");

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  Serial.println("init succeeded");

  

  
  while (!rf95.init()) {
    Serial.println("LoRa radio init failed");
    Serial.println("Uncomment '#define SERIAL_DEBUG' in RH_RF95.cpp for detailed debug info");
    while (1);
  }
  Serial.println("LoRa radio init OK!");

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);
  
  // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on
  // rf95.setModemConfig(RH_RF95::Bw31_25Cr48Sf512);
  rf95.setModemConfig(RH_RF95::Bw125Cr45Sf128);

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then 
  // you can set transmitter powers from 5 to 23 dBm:
  rf95.setTxPower(23, false);

  
}

int16_t packetnum = 0;  // packet counter, we increment per xmission


uint8_t data[] = "Hello World!";
// Dont put this on the stack:
uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];

void loop()
{

  //if (manager.init())
  //  Serial.println("init succeeded");
  delay(1000); // Wait 1 second between transmits, could also 'sleep' here!
  Serial.println("Transmitting..."); // Send a message to rf95_server
  
  char radiopacket[20] = "Hello World #      ";
  itoa(packetnum++, radiopacket+13, 10);
  Serial.print("Sending "); Serial.println(radiopacket);
  radiopacket[19] = 0;
  
  Serial.println("Sending...");
  delay(10);
  manager.sendto((uint8_t *)radiopacket, 20,SERVER_ADDRESS);
  Serial.println("Waiting for packet 1 to complete..."); 
  delay(10);
  rf95.waitPacketSent();
  
  //manager.sendto(data, sizeof(data), SERVER_ADDRESS);

  //Serial.println("Waiting for packet to complete..."); 
  //delay(10);
  //rf95.waitPacketSent();
  // Now wait for a reply
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  uint8_t len = sizeof(buf);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("Waiting for reply...");
  if (rf95.waitAvailableTimeout(2000))
  { 
    // Should be a reply message for us now   
    if (rf95.recv(buf, &len))
   {
      digitalWrite(LED_BUILTIN, HIGH);
      Serial.print("Got reply: ");
      Serial.println((char*)buf);
      Serial.print("RSSI: ");
      Serial.println(rf95.lastRssi(), DEC);    
    }
    else
    {
      Serial.println("Receive failed");
    }
  }
  else
  {
    Serial.println("No reply, is there a listener around?");
  }

}


*/



/*
// rf95_datagram_client.pde
// -*- mode: C++ -*-
// Example sketch showing how to create a simple addressed, messaging client
// with the RHDatagram class, using the RH_RF95 driver to control a RF95 radio.
// It is designed to work with the other example rf95_datagram_server


#include <RHDatagram.h>
#include <RH_RF95.h>
#include <SPI.h>

#define CLIENT_ADDRESS 1
#define SERVER_ADDRESS 2
// Setup GPIO Pins
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 3

// Change to 434.0 or other frequency, must match RX's freq!
#define RF95_FREQ 868.0

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

//RH_RF95 driver(5, 2); // Rocket Scream Mini Ultra Pro with the RFM95W

// Class to manage message delivery and receipt, using the driver declared above
RHDatagram manager(rf95, CLIENT_ADDRESS);

// Need this on Arduino Zero with SerialUSB port (eg RocketScream Mini Ultra Pro)
//#define Serial SerialUSB

void setup()
{
  // Rocket Scream Mini Ultra Pro with the RFM95W only:
  // Ensure serial flash is not interfering with radio communication on SPI bus
//  pinMode(4, OUTPUT);
//  digitalWrite(4, HIGH);
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  Serial.begin(115200);

  if (!manager.init())
    Serial.println("init failed");
  // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);
  rf95.setTxPower(23, false);
  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then
  // you can set transmitter powers from 5 to 23 dBm:
//  driver.setTxPower(23, false);
  // If you are using Modtronix inAir4 or inAir9,or any other module which uses the
  // transmitter RFO pins and not the PA_BOOST pins
  // then you can configure the power transmitter power for -1 to 14 dBm and with useRFO true.
  // Failure to do that will result in extremely low transmit powers.
//  driver.setTxPower(14, true);
  // You can optionally require this module to wait until Channel Activity
  // Detection shows no activity on the channel before transmitting by setting
  // the CAD timeout to non-zero:
//  driver.setCADTimeout(10000);
}

uint8_t data[] = "Hello World!";
// Dont put this on the stack:
uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];

void loop()
{
  Serial.println("Sending to rf95_reliable_datagram_server");

  // Send a message to manager_server
  manager.sendto(data, sizeof(data), SERVER_ADDRESS);
  if (rf95.waitAvailableTimeout(5000))
    {
    // Now wait for a reply from the server
    uint8_t len = sizeof(buf);
    uint8_t from;
    if (manager.recvfrom(buf, &len, &from))
    {
      Serial.print("got reply from : 0x");
      Serial.print(from, HEX);
      Serial.print(": ");
      Serial.println((char*)buf);
    }
    else
    {
      Serial.println("No reply, is rf95_datagram_server running?");
    }
  }
  else
    Serial.println("sendto failed");
  delay(2000);
}

*/
