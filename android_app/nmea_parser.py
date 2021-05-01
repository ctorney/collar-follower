
import pynmea2

class parseNMEA():

    def __init__(self):

        self.latitude = None
        self.longitude = None
        self.acc = 1.0
        self.alt = 1.0

        self.has_fix = False


    def parse_msg(self,msg):
        try:
            msgtxt = msg.decode("UTF-8")
            sentence = msgtxt.strip().strip('\n')
            parsed = pynmea2.parse(sentence)
        except:
            return False


        try:
            if parsed.sentence_type == "GLL": 
                pass # not handled
            elif parsed.sentence_type == "RMC":  # Minimum location info
                if parsed.status=='A':   # Status Valid(A) or Invalid(V)
                    self.has_fix = True

                    # Latitude
                    self.latitude = parsed.latitude 

                    # Longitude
                    self.longitude = parsed.longitude 
            elif parsed.sentence_type == "GGA":  # 3D location fix
                if parsed.gps_qual>0:
                    self.has_fix = True

                    # Latitude
                    self.latitude = parsed.latitude 

                    # Longitude
                    self.longitude = parsed.longitude 

                    self.alt = parsed.altitude

                    self.num_sats = parsed.num_sats
            elif parsed.sentence_type == "GSV":  # Satellites in view
                self.num_sats = parsed.num_sv_in_view

            elif parsed.sentence_type == "GSA":  # GPS DOP and active satellites
                self.acc = parsed.hdop 
        except:
            return False

        
        return True

