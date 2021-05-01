from oscpy.server import OSCThreadServer
from time import sleep
from oscpy.client import OSCClient
import change_gps
import pynmea2
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

        self.first_fix=False
        self.latitude = None
        self.longitude = None
        self.has_fix = False
        


    def gps_button_callback(self,values):
        self.spoofGPS = values
        if self.spoofGPS:
            self.send_msg('GPS spoofing started') 
        else:
            self.send_msg('GPS spoofing stopped') 

    def parse_msg(self,msg):
        try:
            msgtxt = msg.decode("UTF-8")
            sentence = msgtxt.strip().strip('\n')
            parsed = pynmea2.parse(sentence)
        except:
            return False


        try:
            if parsed.sentence_type == "RMC":  # Minimum location info
                if parsed.status=='A':   # Status Valid(A) or Invalid(V)
                    self.has_fix = True
                    # Latitude
                    self.latitude = parsed.latitude 
                    # Longitude
                    self.longitude = parsed.longitude 
        except:
            return False

        
        return True

    def ble_msg(self,values):
        try:
            ss = self.parse_msg(values)
            if self.has_fix:
                if not self.first_fix:
                    self.first_fix = True
                    self.send_msg('Tag has GPS fix') 
        except:
            pass

    def run(self):
        while True:
            if self.spoofGPS and self.has_fix:
                try: 
                    self.gps.update_locale(self.latitude,self.longitude)
                except:
                    pass

            sleep(.1)

    def send_msg(self, text):
        self.client.send_message(b'/msg', [text.encode()])


if __name__ == '__main__':
    service = serviceRunner()
    service.run()


