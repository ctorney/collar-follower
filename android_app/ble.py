
from able import BluetoothDispatcher, GATT_SUCCESS
from jnius import autoclass
from oscpy.client import OSCClient

UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

autoclass('org.jnius.NativeInvocationHandler')


class BLE(BluetoothDispatcher):


    def __init__(self):
        super(BLE, self).__init__()
        self.gps_client = OSCClient(b'localhost', 3000)
        self.app_client = OSCClient(b'localhost', 3001)
        self.connected=False

    
    def connect(self):
        self.send_app_msg('Starting bluetooth scan...') 
        self.start_scan()  # start a scan for devices

    def on_device(self, device, rssi, advertisement):
        # some device is found during the scan
        name = device.getName()
        if name and name.startswith('CIRCUITPY'):  # is an adafruit device

            self.send_app_msg('Found device named ' + name) 
            self.device = device
            self.stop_scan()

    def disconnect(self):
        self.stop_scan()
        self.close_gatt()  # close current connection
        self.device = None
        self.connected=False
        self.send_app_msg('No device: Disconnected from Bluetooth') 

    def on_scan_completed(self):
        if self.device:
            self.connect_gatt(self.device)  # connect to device
        else:
            self.send_app_msg('No device: Scan completed and no suitable bluetooth device detected') 

    def on_connection_state_change(self, status, state):
        if status == GATT_SUCCESS and state:  # connection established
            self.send_app_msg('Connected to device ' + self.device.name) 
            self.discover_services()  # discover what services a device offer
            self.connected=True
        else:  # disconnection or error
            self.send_app_msg('No device: Disconnected from Bluetooth') 
            self.close_gatt()  # close current connection
            self.connected=False

    def on_services(self, status, services):
        self.tx_characteristic = services.search(UART_TX_CHAR_UUID)  # get device transmitter 
        # self.rx_characteristic = services.search(UART_RX_CHAR_UUID)  # get device receiver (in case we want to send messages in future)
        self.enable_notifications(self.tx_characteristic)   # listen for any message transmitted

    def on_characteristic_changed(self, characteristic):
        # message received so forward to the GPS service
        value = characteristic.getValue()
        self.gps_client.send_message(b'/blemsg', [bytes(value)])

    def send_app_msg(self, text):
        # send log messages back to the main app
        self.app_client.send_message(b'/ble', [text.encode()])



