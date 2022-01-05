

from plyer.facades import GPS
from plyer.platforms.android import activity
from jnius import autoclass, java_method, PythonJavaClass

import time
Looper = autoclass('android.os.Looper')
SystemClock = autoclass('android.os.SystemClock')
LocationManager = autoclass('android.location.LocationManager')
Location = autoclass('android.location.Location')
Context = autoclass('android.content.Context')
System = autoclass('java.lang.System')


# GPS spoofer with alpha-beta filter
class changeGPS():

    def __init__(self, alpha=0.95, beta=0.8):

        self.lm = activity.getSystemService(Context.LOCATION_SERVICE)

        self.providerName  = LocationManager.GPS_PROVIDER

        try:
            self.lm.removeTestProvider(self.providerName)
        except:
            pass
        self.lm.addTestProvider(self.providerName, False, False, False, False, False, True, True, 1, 2)
        self.lm.setTestProviderEnabled(self.providerName, True)


        # alpha-beta filter
        self.alpha = alpha
        self.beta = beta

        self.last_lat = None
        self.last_lon = None

        self.update_time = None

        self.speed_lat = 0.0
        self.speed_lon = 0.0

        self.delay_time = 2.0 # seconds to add to account for the delay in transmitting the location

    
    def add_location(self, lat, lon):


        time_now = time.monotonic() - self.delay_time

        if self.update_time is None:
            # first update
            self.update_time = time_now
            self.last_lat = lat
            self.last_lon = lon
            return

        pred_lat, pred_lon = self.predict(time_now)
        
        delta_t = time_now - self.update_time

        error_lat = lat - pred_lat
        error_lon = lon - pred_lon

        self.last_lat = pred_lat + self.alpha * error_lat
        self.last_lon = pred_lon + self.alpha * error_lon
      
        self.speed_lat = self.speed_lat + (self.beta / delta_t) * error_lat
        self.speed_lon = self.speed_lon + (self.beta / delta_t) * error_lon

        self.update_time = time_now
        return 

    def predict(self, t=None):

        if t is None:
            t = time.monotonic()

        delta_t = t - self.update_time
        pred_lat = self.last_lat + (delta_t * self.speed_lat)
        pred_lon = self.last_lon + (delta_t * self.speed_lon)

        return pred_lat, pred_lon



    def update_locale(self):

        lat, lon = self.predict()
           
        mockLocation = Location(self.providerName)
        mockLocation.setLatitude(lat)
        mockLocation.setLongitude(lon)
        mockLocation.setAltitude(1.0)
        mockLocation.setTime(System.currentTimeMillis())
        mockLocation.setSpeed(0.0)
        mockLocation.setBearing(1)
        mockLocation.setAccuracy(1.8)
        mockLocation.setBearingAccuracyDegrees(0.1)
        mockLocation.setVerticalAccuracyMeters(0.1)
        mockLocation.setSpeedAccuracyMetersPerSecond(0.01)
        mockLocation.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos())
        self.lm.setTestProviderLocation(self.providerName, mockLocation)

        return
