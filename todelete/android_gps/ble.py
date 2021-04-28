
from able import BluetoothDispatcher, GATT_SUCCESS
from jnius import autoclass
from oscpy.client import OSCClient

UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"


#from error_message import install_exception_handler
autoclass('org.jnius.NativeInvocationHandler')


class BLE(BluetoothDispatcher):


    def __init__(self):
        super(BLE, self).__init__()
        self.gps_client = OSCClient(b'localhost', 3000)
        self.app_client = OSCClient(b'localhost', 3001)

    
    def connect(self):
        #if self.alert_characteristic:  # alert service is already discovered
        #    self.alert(self.alert_characteristic)
        #elif self.device:  # device is already founded during the scan
        #    self.connect_gatt(self.device)  # reconnect
        #else:
        #    self.stop_scan()  # stop previous scan
        self.send_app_msg('Starting bluetooth scan...') 
        self.start_scan()  # start a scan for devices#

    def on_device(self, device, rssi, advertisement):
        # some device is found during the scan
        name = device.getName()
        if name and name.startswith('Bluefruit'):  # is a Mi Band device

            self.send_app_msg('Found device named ' + name) 
            self.device = device
            self.stop_scan()

    def disconnect(self):
        self.stop_scan()
        self.close_gatt()  # close current connection
        self.device = None

    def on_scan_completed(self):
        if self.device:
            self.connect_gatt(self.device)  # connect to device
        else:
            self.send_app_msg('No device: Scan completed and no suitable bluetooth device detected') 

    def on_connection_state_change(self, status, state):
        if status == GATT_SUCCESS and state:  # connection established
            self.send_app_msg('Connected to device ' + self.device.name) 
            self.discover_services()  # discover what services a device offer
        else:  # disconnection or error
            self.send_app_msg('No device: Disconnected from Bluetooth') 
            self.close_gatt()  # close current connection

    def on_services(self, status, services):
        # 0x2a06 is a standard code for "Alert Level" characteristic
        # https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.alert_level.xml
        self.tx_characteristic = services.search(UART_TX_CHAR_UUID)
        self.rx_characteristic = services.search(UART_RX_CHAR_UUID)
        self.enable_notifications(self.tx_characteristic)
        #print(self.alert_characteristic)
        #self.alert()#self.alert_characteristic)

    #def on_characteristic_read(self, characteristic, status):
    #    if status == GATT_SUCCESS:  # connection established
    #        aa = characteristic.getValue()#.decode())#, [2])  # 2 is for "High Alert"
    #        print(aa)

    def on_characteristic_changed(self, characteristic):
        value = characteristic.getValue()
        #print(bytes(value).decode())
        self.gps_client.send_message(b'/blemsg', [bytes(value)])#, ip_address=b'localhost', port=3000) 

    def send_app_msg(self, text):
        self.app_client.send_message(b'/msg', [text.encode()])#, ip_address=b'localhost', port=3000) 

    #def alert(self):
    #    print('do nothing')
    #    print(self.write_characteristic(self.rx_characteristic, [2]))  # 2 is for "High Alert"
        #while True:
        #    self.read_characteristic(self.tx_characteristic)#, [2])  # 2 is for "High Alert"
            #aa = self.tx_characteristic.getValue()#.decode())#, [2])  # 2 is for "High Alert"
            #if aa:
            #    print(aa.decode())#, [2])  # 2 is for "High Alert"
        #    sleep(0.1)


