#include <SPI.h>
#include <LoRa.h>

#define DIO0 3
#define SS   8
#define RESET 4

#include <SAMDTimerInterrupt.h>
#include <SAMD_ISR_Timer.h>
#include <Adafruit_GPS.h>


#define GPS_INTERRUPT_MS        10     // 1s = 1000ms
#define NMEA_SENTENCE_MAX_LEN   82     




#define RF95_FREQ 868.0


#define CLIENT_ADDRESS 1
#define SERVER_ADDRESS 2
 
int spreadingFactor =11;
long signalBandwidth = 125E3;
int codingRateDenominator = 5;

// what's the name of the hardware serial port?
#define GPSSerial Serial1

// Connect to the GPS on the hardware port
Adafruit_GPS GPS(&GPSSerial);


uint32_t timer = millis();



byte msgCount = 0;            // count of outgoing messages
byte localAddress = 1;     // address of this device
byte destination = 0;      // destination to send to



void gps_interrupt(void)
{
    GPS.read();
}

void setup()
{
  Serial.begin(115200);
  Serial.println("Adafruit GPS library basic parsing test!");
  // Init timer ITimer1
  SAMDTimer ITimer0(TIMER_TC3);  
//  // Interval in microsecs
  if (ITimer0.attachInterruptInterval(GPS_INTERRUPT_MS * 1000, gps_interrupt))
    Serial.println("Starting  ITimer0 OK, millis() = " + String(millis()));
  else
    Serial.println("Can't set ITimer0. Select another freq. or timer");
  pinMode(LED_BUILTIN, OUTPUT);


  // GPS initialise
  GPS.begin(9600);

  GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCONLY);
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ); // 1 Hz update rate
  //GPS.sendCommand(PMTK_SET_NMEA_UPDATE_100_MILLIHERTZ); // 0.1 Hz update rate
  
  delay(1000);


  // LoRa settings
  //driver.setModemConfig(RH_RF95::Bw125Cr45Sf128);
  //driver.setModemConfig(RH_RF95::Bw31_25Cr48Sf512);
  LoRa.setPins(SS, RESET, DIO0);
  
  if (!LoRa.begin(868E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
  //LoRa.setSpreadingFactor(spreadingFactor);
  LoRa.setSignalBandwidth(signalBandwidth);
  LoRa.setCodingRate4(codingRateDenominator);
  LoRa.setTxPower(20);//, PA_OUTPUT_RFO_PIN);
  LoRa.enableCrc();
  // register the receive callback
  LoRa.onReceive(onReceive);
//  LoRa.onTxDone(onTxDone);
  delay(1000);
  
}

//uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];


//uint8_t data[] = "Hello World!";
int counter = 0;

void loop() // run over and over again
{
  //Serial.println("LOOPY"); // this also sets the newNMEAreceived() flag to false
  delay(10);

  //if (0)
  if (GPS.newNMEAreceived()) {

    
    Serial.println(GPS.lastNMEA()); // this also sets the newNMEAreceived() flag to false

    String sentence = "";                 // payload of packet
    char *nmea = GPS.lastNMEA();

    for (int i = 0; i < NMEA_SENTENCE_MAX_LEN; i++) 
    {
          char curr_char = nmea[i];
          sentence += curr_char;
          if (curr_char == '\n') break;
    }

    sendMessage(sentence);

  
//    LoRa.beginPacket();
//    LoRa.write((uint8_t *)GPS.lastNMEA(), NMEA_SENTENCE_MAX_LEN);
//    LoRa.endPacket();
  //LoRa.beginPacket();
  //LoRa.print("hello ");
  //LoRa.print("hello ");
  //LoRa.print("hello ");
  //LoRa.print("hello ");

  //LoRa.print(sentence);                 // add payload

  //LoRa.print(counter);
  //LoRa.endPacket();

    
  }
////    
  LoRa.receive();
  
}


void sendMessage(String outgoing) {

   while (LoRa.beginPacket() == 0) {
    Serial.print("waiting for radio ... ");
    delay(100);
  }
  LoRa.beginPacket();                   // start packet
  LoRa.write(destination);              // add destination address
  LoRa.write(localAddress);             // add sender address
  LoRa.write(msgCount);                 // add message ID
  LoRa.write(outgoing.length());        // add payload length
  LoRa.print(outgoing);                 // add payload
  LoRa.endPacket();                     // finish packet and send it
  msgCount++;                           // increment message ID
}



//uint8_t buf[20];

//void loop() {
//  Serial.print("Sending packet: ");
//  Serial.println(counter);
//
//  // send packet
//  LoRa.beginPacket();
//  LoRa.print("hello ");
//  LoRa.print(counter);
//  LoRa.endPacket();
//
// 
////  int packetSize = LoRa.parsePacket();
////  if (packetSize) {
////    Serial.print("Received packet: ");
////    String incoming = "";
////  if (LoRa.available())
////  {
////    LoRa.readBytes(buf, packetSize);
////    Serial.println((char*)buf);
////  }
////
////    Serial.print(" with RSSI ");
////    Serial.println(LoRa.packetRssi());
////
////  }
//
//  counter++;
//
//  delay(1000);
//}



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

  //if (incomingLength != incoming.length()) {   // check length for error
  //  Serial.println("error: message length does not match length");
  //  return;                             // skip rest of function
  //}

  // if the recipient isn't this device or broadcast,
  if (recipient != localAddress && recipient != 0xFF) {
    Serial.println("This message is not for me.");
    return;                             // skip rest of function
  }

  // if message is for this device, or broadcast, print details:
  Serial.println("Received from: 0x" + String(sender, HEX));
  Serial.println("Sent to: 0x" + String(recipient, HEX));
  Serial.println("Message ID: " + String(incomingMsgId));
  Serial.println("Message length: " + String(incomingLength));
  Serial.println("Message: " + incoming);
  Serial.println("RSSI: " + String(LoRa.packetRssi()));
  Serial.println("Snr: " + String(LoRa.packetSnr()));
  Serial.println();
}


void onReceive2(int packetSize) {
  // received a packet
  Serial.print("Received packet '");

  // read packet
  for (int i = 0; i < packetSize; i++) {
    Serial.print((char)LoRa.read());
  }

  // print RSSI of packet
  Serial.print("' with RSSI ");
  Serial.println(LoRa.packetRssi());
}
