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
        self.first_fix=False
        


    def gps_button_callback(self,values):
        self.spoofGPS = values
        if self.spoofGPS:
            self.send_msg('GPS spoofing started') 
        else:
            self.send_msg('GPS spoofing stopped') 


    def ble_msg(self,values):
        try:
            ss = self.parser.parse_msg(values)
            if self.parser.has_fix:
                if not self.first_fix:
                    self.first_fix = True
                    self.send_msg('Tag has GPS fix') 
        except:
            pass

    def run(self):
        while True:
            if self.spoofGPS:

                if self.parser.has_fix:
                    try: 
                        self.gps.update_locale(self.parser.latitude,self.parser.longitude, self.parser.alt, self.parser.acc)
                    except:
                        pass

            sleep(.1)

    def send_msg(self, text):
        self.client.send_message(b'/msg', [text.encode()])


if __name__ == '__main__':


    service = serviceRunner()

    service.run()


