from time import sleep
from oscpy.server import OSCThreadServer
from time import sleep
import change_gps

class serviceRunner():
    def __init__(self):

        self.spoofGPS = False
        self.osc = OSCThreadServer()
        self.sock = self.osc.listen(address=b'localhost', port=3000, default=True)
        self.osc.bind(b'/button', self.button_callback)

        self.gps = change_gps.changeGPS()

    def button_callback(self,values):
        self.spoofGPS = values
        print('msg: ',values, self.spoofGPS)

    def run(self):
        while True:
            if self.spoofGPS:
                print("updating gps...")
                lat = -2.332577
                lon = 34.832153

                self.gps.update_locale(lat,lon)

            sleep(.1)


if __name__ == '__main__':


    service = serviceRunner()

    service.run()


