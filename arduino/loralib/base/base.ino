
#include <SPI.h>
#include <LoRa.h>


#include <bluefruit.h>


#define DIO0 6
#define SS   10
#define RESET 11


 
int spreadingFactor =11;
long signalBandwidth = 125E3;
int codingRateDenominator = 5;


BLEUart bleuart;

void setup() {

  Serial.begin(115200);
  delay(1000);
  //while (!Serial);

  Serial.println("LoRa Receiver");
  LoRa.setPins(SS, RESET, DIO0);

  LoRa.setSpreadingFactor(spreadingFactor);
  LoRa.setSignalBandwidth(signalBandwidth);
  LoRa.setCodingRate4(codingRateDenominator);
  LoRa.setTxPower(20, PA_OUTPUT_RFO_PIN);
  if (!LoRa.begin(868E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }

  Bluefruit.autoConnLed(true);
  Bluefruit.begin();
  Bluefruit.setName("Bluefruit52");

  // Configure and Start BLE Uart Service
  bleuart.begin();

  // Set up Advertising Packet
//  //Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
  Bluefruit.Advertising.addTxPower();

  // Include bleuart 128-bit uuid
  Bluefruit.Advertising.addService(bleuart);

  // There is no room for Name in Advertising packet
  // Use Scan response for Name
  Bluefruit.ScanResponse.addName();

  // Start Advertising
  Bluefruit.Advertising.start();

    Serial.println("Setup complete");


}

int RH_RF95_MAX_MESSAGE_LEN=20;

#define MAX_PKT_LENGTH           255
uint8_t buf[MAX_PKT_LENGTH];



void loop() {
//  // try to parse packet
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
//    // received a packet
    Serial.print("Received packet: ");

// read packet header bytes:
  int recipient = LoRa.read();          // recipient address
  byte sender = LoRa.read();            // sender address
  byte incomingMsgId = LoRa.read();     // incoming msg ID
  byte incomingLength = LoRa.read();    // incoming msg length

  String incoming = "";                 // payload of packet

  //while (LoRa.available()) {            // can't use readString() in callback, so
  //  incoming += (char)LoRa.read();      // add bytes one by one
  //}
  int i = 0 ;
  while (LoRa.available())
  {
    buf[i++] = LoRa.read();//Bytes(buf, packetSize);
    
  }
  Serial.println((char*)buf);
    Serial.println(i, DEC);
    Serial.println(incomingLength, DEC);

  if (incomingLength != i) {   // check length for error
    Serial.println("error: message length does not match length");
    return;                             // skip rest of function
  }

    Serial.println(incoming);
    if (Bluefruit.connected()) // bleuart.write(buf,incomingLength);
      for (int i = 0; i < incomingLength; i++) 
       bleuart.write(buf[i]);

    
  //  String incoming = "";
  //if (LoRa.available())
  //{
  //  LoRa.readBytes(buf, packetSize);
  //  Serial.println((char*)buf);
  //}
//  //while (LoRa.available()) {
//  //  incoming += (char)LoRa.read();
//  //}
//    
//    //  Serial.println(incoming);
    //delay(100);
  //  if (Bluefruit.connected()) 
  //    for (int i = 0; i < packetSize; i++) 
  //      bleuart.write(buf[i]);
    //delay(100);

//
//    // print RSSI of packet
    Serial.println(packetSize, DEC);
        Serial.println(incomingLength, DEC);

    Serial.print(" with RSSI ");

    Serial.println(LoRa.packetRssi());

    LoRa.beginPacket();
    LoRa.print("hello back!\n ");
  
    LoRa.endPacket();
  }

  // put the radio into receive mode
  //LoRa.receive();

//  delay(1000);
//
//LoRa.idle();
//digitalWrite(ledPin, state);
}
