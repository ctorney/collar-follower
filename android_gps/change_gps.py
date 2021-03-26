from kivy.lang import Builder
from kivy.app import App
from kivy.properties import StringProperty
from kivy.clock import mainthread
from kivy.utils import platform


from plyer.facades import GPS
from plyer.platforms.android import activity
from jnius import autoclass, java_method, PythonJavaClass

Looper = autoclass('android.os.Looper')
SystemClock = autoclass('android.os.SystemClock')
LocationManager = autoclass('android.location.LocationManager')
Location = autoclass('android.location.Location')
Context = autoclass('android.content.Context')
System = autoclass('java.lang.System')

class changeGPS():

    def __init__(self):

        self.lm = activity.getSystemService(Context.LOCATION_SERVICE)

        self.providerName  = LocationManager.GPS_PROVIDER

        try:
            self.lm.removeTestProvider(self.providerName)
        except:
            pass
        self.lm.addTestProvider(self.providerName, False, False, False, False, False, True, True, 1, 2)
        self.lm.setTestProviderEnabled(self.providerName, True)


    def update_locale(self, lat,lon):
        mockLocation = Location(self.providerName)
        mockLocation.setLatitude(lat)
        mockLocation.setLongitude(lon)
        mockLocation.setAltitude(3.)
        mockLocation.setTime(System.currentTimeMillis())
        mockLocation.setSpeed(0.0)
        mockLocation.setBearing(1)
        mockLocation.setAccuracy(3.)
        mockLocation.setBearingAccuracyDegrees(0.1)
        mockLocation.setVerticalAccuracyMeters(0.1)
        mockLocation.setSpeedAccuracyMetersPerSecond(0.01)
        mockLocation.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos())
        self.lm.setTestProviderLocation(self.providerName, mockLocation)

