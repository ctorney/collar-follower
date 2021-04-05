
#import kivy
from kivy.app import App
#from kivy.clock import Clock

from time import sleep
from kivy.uix.switch import Switch
#from kivy.uix.gridlayout import GridLayout
#from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
#from kivy.lang import Builder
from jnius import autoclass
from oscpy.client import OSCClient
import android

#from plyer.platforms.android import activity
#from plyer.facades import Bluetooth

#Global = autoclass('android.provider.Settings$Global')

#from kivy.graphics import Color, Rectangle

from kivy.core.window import Window

from datetime import datetime
from oscpy.server import OSCThreadServer
#from bleak import BleakScanner, BleakClient

UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
class gui(BoxLayout):

    def __init__(self, gps_switch_callback, ble_switch_callback, **kwargs):

        super(gui, self).__init__(orientation='vertical',**kwargs)


        w,h = Window.size

        horizontalBox   = BoxLayout(orientation='horizontal',size_hint_y=0.25)

        self.ble_info = Label(text="Connect to bluetooth:")
        horizontalBox.add_widget(self.ble_info)

        self.ble_switch = Switch(active=False)

        horizontalBox.add_widget(self.ble_switch)

        self.ble_switch.bind(active=ble_switch_callback)

        horizontalBox.add_widget(Label(text="Start GPS spoofing:"))

        self.gps_switch = Switch(active=False)

        horizontalBox.add_widget(self.gps_switch)

        self.gps_switch.bind(active=gps_switch_callback)
        self.add_widget(horizontalBox)

        self.scrollview = ScrollView(do_scroll_x=True, scroll_type=["bars","content"],size_hint_y=0.75)#, height=0.5*h)
        self.messages = Label(text="",font_size="20sp", text_size=(int(0.9*w), None), size_hint=(1,None))#, height=0.5*h)

        self.messages.bind(texture_size=lambda *x: self.messages.setter('height')(self.messages, self.messages.texture_size[1]))

        self.scrollview.add_widget(self.messages)
        self.add_widget(self.scrollview)




from able import BluetoothDispatcher, GATT_SUCCESS
#from error_message import install_exception_handler
autoclass('org.jnius.NativeInvocationHandler')

from android.runnable import run_on_ui_thread

class BLE(BluetoothDispatcher):

    device = alert_characteristic = None#

    def __init__(self):
        super(BLE, self).__init__()

    def start_alert(self, *args, **kwargs):
        #if self.alert_characteristic:  # alert service is already discovered
        #    self.alert(self.alert_characteristic)
        #elif self.device:  # device is already founded during the scan
        #    self.connect_gatt(self.device)  # reconnect
        #else:
        #    self.stop_scan()  # stop previous scan
        self.start_scan()  # start a scan for devices#

    def on_device(self, device, rssi, advertisement):
        # some device is found during the scan
        name = device.getName()
        if name and name.startswith('Bluefruit'):  # is a Mi Band device

            print('got a device:', device.name)
            self.device = device
            self.stop_scan()

    def on_scan_completed(self):
        if self.device:
            self.connect_gatt(self.device)  # connect to device

    def on_connection_state_change(self, status, state):
        if status == GATT_SUCCESS and state:  # connection established
            self.discover_services()  # discover what services a device offer
        else:  # disconnection or error
            self.alert_characteristic = None
            self.close_gatt()  # close current connection

    def on_services(self, status, services):
        # 0x2a06 is a standard code for "Alert Level" characteristic
        # https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.alert_level.xml
        print(services)
        self.tx_characteristic = services.search(UART_TX_CHAR_UUID)
        self.rx_characteristic = services.search(UART_RX_CHAR_UUID)
        self.enable_notifications(self.tx_characteristic)
        #print(self.alert_characteristic)
        self.alert()#self.alert_characteristic)

    def on_characteristic_read(self, characteristic, status):
        if status == GATT_SUCCESS:  # connection established
            aa = characteristic.getValue()#.decode())#, [2])  # 2 is for "High Alert"
            print(aa)

    def on_characteristic_changed(self, characteristic):
        value = characteristic.getValue()
        print(bytes(value).decode())

    def alert(self):
        print('do nothing')
        print(self.write_characteristic(self.rx_characteristic, [2]))  # 2 is for "High Alert"
        #while True:
        #    self.read_characteristic(self.tx_characteristic)#, [2])  # 2 is for "High Alert"
            #aa = self.tx_characteristic.getValue()#.decode())#, [2])  # 2 is for "High Alert"
            #if aa:
            #    print(aa.decode())#, [2])  # 2 is for "High Alert"
        #    sleep(0.1)



class collarFollower(App):
    def request_android_permissions(self):
        """
        Since API 23, Android requires permission to be requested at runtime.
        This function requests permission and handles the response via a
        callback.

        The request will produce a popup if permissions have not already been
        been granted, otherwise it will do nothing.
        """
        from android.permissions import request_permissions, Permission

        def callback(permissions, results):
            """
            Defines the callback to be fired when runtime permission
            has been granted or denied. This is not strictly required,
            but added for the sake of completeness.
            """
            if all([res for res in results]):
                print("callback. All permissions granted.")
            else:
                print("callback. Some permissions refused.")

        request_permissions([Permission.ACCESS_COARSE_LOCATION,
                                Permission.BLUETOOTH,
                                Permission.BLUETOOTH_ADMIN,
                                Permission.ACCESS_FINE_LOCATION], callback)

    def build(self):
        #service = android.start_service(title='GPS spoofer service',
        #              description='service for switching  description',
        #              arg='')
        #self.service = service
        

        autoclass('org.able.PythonBluetooth')
        SERVICE_NAME = u'{packagename}.Service{servicename}'.format(
        packagename=u'org.kivy.collarfollower',
        servicename=u'Myservice')
        service = autoclass(SERVICE_NAME)
        self.mActivity = autoclass(u'org.kivy.android.PythonActivity').mActivity
        argument = ''
        service.start(self.mActivity, argument)

        #self.something = autoclass('collarfollower.PythonScanCallback')
        #service = autoclass('your.package.domain.package.name.ServiceMyservice')
        #mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
        #argument = ''
        #service.start(mActivity, argument)
        self.service = service

        self.client = OSCClient(b'localhost', 3000)
        self.osc = OSCThreadServer()
        self.sock = self.osc.listen(address=b'localhost', port=3001, default=True)
        self.osc.bind(b'/msg', self.service_msg_callback)

        self.ble = BLE()
 
        return gui(self.gps_switch_callback, self.ble_switch_callback)

    @run_on_ui_thread
    def init(self, *args, **kwargs):
        self.ble = BLE()

    def gps_switch_callback(self, switchObject, switchValue):

        #print('Value of gps settings is:', switchValue)
        self.client.send_message(b'/gpsbutton', [switchValue])


    #@run_on_ui_thread
    def ble_switch_callback(self, switchObject, switchValue):

 #       bluetooth_enabled = Global.getString(activity.getContentResolver(),Global.BLUETOOTH_ON)


 #       if switchValue:
 #           if int(bluetooth_enabled)==0:
 #               self.write_msg('Bluetooth is currently inactive. Please enable in order to connect.')
 #               self.root.ble_switch.active=False
 #               return
        self.ble.start_alert()

        #self.client.send_message(b'/blebutton', [switchValue])


    def service_msg_callback(self,values):
        self.write_msg(values.decode())

    def write_msg(self, text):
        self.root.messages.text = "[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] " + text + "\n" + self.root.messages.text
        

    def on_stop(self):
        self.service.stop(self.mActivity)
        self.ble.stop_scan()
        return

    def on_pause(self):
        return True
    

if __name__ == '__main__':
    collarFollower().run()
