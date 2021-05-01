
import pynmea2

class parseNMEA():

    def __init__(self):

        self.latitude = None
        self.longitude = None
        self.has_fix = False


    def parse_msg(self,msg):
        try:
            msgtxt = msg.decode("UTF-8")
            sentence = msgtxt.strip().strip('\n')
            parsed = pynmea2.parse(sentence)
        except:
            return False


        try:
            if parsed.sentence_type == "RMC":  # Minimum location info
                if parsed.status=='A':   # Status Valid(A) or Invalid(V)
                    self.has_fix = True
                    # Latitude
                    self.latitude = parsed.latitude 
                    # Longitude
                    self.longitude = parsed.longitude 
        except:
            return False

        
        return True

