
import kivy
from kivy.app import App
from kivy.clock import Clock

from kivy.uix.switch import Switch
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder
from jnius import autoclass
from oscpy.client import OSCClient
import android


from kivy.graphics import Color, Rectangle

from kivy.core.window import Window

from datetime import datetime

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
        self.messages = Label(text="..",font_size="20sp", text_size=(int(0.9*w), None), size_hint=(1,None))#, height=0.5*h)

        self.messages.bind(texture_size=lambda *x: self.messages.setter('height')(self.messages, self.messages.texture_size[1]))

        self.scrollview.add_widget(self.messages)
        self.add_widget(self.scrollview)





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
                             Permission.ACCESS_FINE_LOCATION], callback)

    def build(self):
        service = android.start_service(title='GPS spoofer service',
                      description='service for switching  description',
                      arg='')
        self.service = service

        self.client = OSCClient(b'localhost', 3000)
 
        return gui(self.gps_switch_callback, self.ble_switch_callback)

    def gps_switch_callback(self, switchObject, switchValue):

        print('Value of gps settings is:', switchValue)
        #self.client.send_message(b'/button', [switchValue])  # uncomment to enable spoofing

        self.root.messages.text = "[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] Here's another message from the device.\n" + self.root.messages.text

    def ble_switch_callback(self, switchObject, switchValue):

        if switchValue:
            self.root.ble_info.text = 'Connecting....'
        else:
            self.root.ble_info.text = 'Connect to bluetooth:'

        self.root.messages.text = "[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] Here's another message from the device.\n" + self.root.messages.text
        print('Value of ble sample settings is:', switchValue)

    def on_start(self):
        return

    def on_pause(self):
        return True
    

if __name__ == '__main__':
    collarFollower().run()
