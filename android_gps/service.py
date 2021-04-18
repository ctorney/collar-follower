from oscpy.server import OSCThreadServer
from time import sleep
from oscpy.client import OSCClient
import change_gps
#import bt_relay
import asyncio
from jnius import autoclass

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
        #self.bt = bt_relay.btRelay()

    def gps_button_callback(self,values):
        self.spoofGPS = values
        if self.spoofGPS:
            self.send_msg('GPS spoofing started') 
        else:
            self.send_msg('GPS spoofing stopped') 

    #def scan(self):
    #    try:

    #        autoclass('org.able.PythonBluetooth')
    #        self.ble = BLE()
            #self.ble.start_alert()
            #loop = asyncio.get_event_loop()
            #asyncio.run(run())# loop.run_until_complete(run())

    #    except Exception as e:
    #        self.send_msg(str(e)) 
    #        pass
        #print('imported ',values)
    #    self.send_msg('imported') 


    def ble_msg(self,values):
        self.send_msg('gps received from ble: ' + values.decode()) 
        self.offset_test+=0.01
        #self.scan()
        #pass
        #self.bt.scan()

    def run(self):
        while True:
            if self.spoofGPS:
                print("updating gps...")
                lat = -2.332577+self.offset_test
                lon = 34.832153

                self.gps.update_locale(lat,lon)

            sleep(.1)

    def send_msg(self, text):
        self.client.send_message(b'/msg', [text.encode()])#, ip_address=b'localhost', port=3000) 


if __name__ == '__main__':


    service = serviceRunner()

    service.run()


