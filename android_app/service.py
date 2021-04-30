from oscpy.server import OSCThreadServer
from time import sleep
from oscpy.client import OSCClient
import change_gps
import nmea_parser
import asyncio
from jnius import autoclass

DEBUG = 1 # print all messages to the app

class serviceRunner():
    def __init__(self):

        self.spoofGPS = False
        self.osc = OSCThreadServer()
        self.sock = self.osc.listen(address=b'localhost', port=3000, default=True)
        self.osc.bind(b'/gpsbutton', self.gps_button_callback)
        self.osc.bind(b'/blemsg', self.ble_msg)

        self.client = OSCClient(b'localhost', 3001)
        self.gps = change_gps.changeGPS()
        self.parser = nmea_parser.parseNMEA()
        self.offset_test=0.0
        


    def gps_button_callback(self,values):
        self.spoofGPS = values
        if self.spoofGPS:
            self.send_msg('GPS spoofing started') 
        else:
            self.send_msg('GPS spoofing stopped') 


    def ble_msg(self,values):
        self.send_msg('BLE msg: ' + values.decode()) 
        try:
            ss = self.parser.parse_msg(values)
            if ss=="SUCCESS":
                self.send_msg((str(self.parser.latitude) + ' ' + str(self.parser.longitude)))
            self.send_msg('Parser: ' + ss) 
            #msgtxt = values.decode("UTF-8")
            #msgtxt = msgtxt.split(',')
            #if msgtxt[0]=="LAT":
            #    self.lat = float(msgtxt[1])
            #    if DEBUG:
            #        self.send_msg('Received latitude value: ' + msgtxt[1]) 
            #elif msgtxt[0]=="LON":
            #    self.lon = float(msgtxt[1])
            #    if DEBUG:
            #        self.send_msg('Received longitude value: ' + msgtxt[1]) 
            #
            #else:
        except:
            pass

    def run(self):
        while True:
            if self.spoofGPS:
                #lat = -2.332577
                #lon = 34.832153

                #self.gps.update_locale(lat,lon)

                if self.parser.has_fix:
                    try: 
                        print('spoof')#self.gps.update_locale(self.parser.lat,self.parser.lon, self.parser.alt, self.parser.acc)
                        self.gps.update_locale(self.parser.latitude,self.parser.longitude, self.parser.alt, self.parser.acc)
                    except:
                        pass

            sleep(.1)

    def send_msg(self, text):
        self.client.send_message(b'/msg', [text.encode()])#, ip_address=b'localhost', port=3000) 


if __name__ == '__main__':


    service = serviceRunner()

    service.run()


