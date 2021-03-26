
import kivy
from kivy.app import App
from kivy.clock import Clock

from kivy.uix.switch import Switch
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.lang import Builder
from jnius import autoclass
from oscpy.client import OSCClient
import android


# A Gridlayout with a label a switch
class gui(GridLayout):

     def __init__(self, switch_callback, **kwargs):

          super(gui, self).__init__(**kwargs)

          self.cols = 2

          self.add_widget(Label(text="Spoof GPS:"))

          self.settings_sample = Switch(active=False)

          self.add_widget(self.settings_sample)

          self.settings_sample.bind(active=switch_callback)





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
        return gui(self.switch_callback)

    def switch_callback(self, switchObject, switchValue):

        print('Value of sample settings is:', switchValue)
        self.client.send_message(b'/button', [switchValue])


    def on_pause(self):
        return True
    

if __name__ == '__main__':
    collarFollower().run()
