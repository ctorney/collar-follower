from oscpy.server import OSCThreadServer
from time import sleep
from oscpy.client import OSCClient
import change_gps
#import bt_relay
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
        self.offset_test=0.0
        

        self.lat = None
        self.lon = None

    def gps_button_callback(self,values):
        self.spoofGPS = values
        if self.spoofGPS:
            self.send_msg('GPS spoofing started') 
        else:
            self.send_msg('GPS spoofing stopped') 


    def ble_msg(self,values):
        try:
            msgtxt = values.decode("UTF-8")
            msgtxt = msgtxt.split(',')
            if msgtxt[0]=="LAT":
                self.lat = float(msgtxt[1])
                if DEBUG:
                    self.send_msg('Received latitude value: ' + msgtxt[1]) 
            elif msgtxt[0]=="LON":
                self.lon = float(msgtxt[1])
                if DEBUG:
                    self.send_msg('Received longitude value: ' + msgtxt[1]) 

            else:
                self.send_msg('BLE msg: ' + values.decode()) 
        except:
            pass

    def run(self):
        while True:
            if self.spoofGPS:
                #lat = -2.332577
                #lon = 34.832153

                #self.gps.update_locale(lat,lon)

                if self.lat is not None and self.lon is not None:
                    try: 
                        self.gps.update_locale(self.lat,self.lon)
                    except:
                        pass

            sleep(.1)

    def send_msg(self, text):
        self.client.send_message(b'/msg', [text.encode()])#, ip_address=b'localhost', port=3000) 


if __name__ == '__main__':


    service = serviceRunner()

    service.run()


