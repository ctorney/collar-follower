
_GLL = 0
_RMC = 1
_GGA = 2
_GSA = 3
_GSA_4_11 = 4
_GSV7 = 5
_GSV11 = 6
_GSV15 = 7
_GSV19 = 8
_ST_MIN = _GLL
_ST_MAX = _GSV19

_SENTENCE_PARAMS = (
    # 0 - _GLL
    "dcdcfcC",
    # 1 - _RMC
    "fcdcdcffiDCC",
    # 2 - _GGA
    "fdcdciiffsfsIS",
    # 3 - _GSA
    "ciIIIIIIIIIIIIfff",
    # 4 - _GSA_4_11
    "ciIIIIIIIIIIIIfffS",
    # 5 - _GSV7
    "iiiiiiI",
    # 6 - _GSV11
    "iiiiiiIiiiI",
    # 7 - _GSV15
    "iiiiiiIiiiIiiiI",
    # 8 - _GSV19
    "iiiiiiIiiiIiiiIiiiI",
)

def _parse_degrees(nmea_data):
    # Parse a NMEA lat/long data pair 'dddmm.mmmm' into a pure degrees value.
    # Where ddd is the degrees, mm.mmmm is the minutes.
    if nmea_data is None or len(nmea_data) < 3:
        return None
    raw = float(nmea_data)
    deg = raw // 100
    minutes = raw % 100
    return deg + minutes / 60


def _parse_data(sentence_type, data):
    """Parse sentence data for the specified sentence type and
    return a list of parameters in the correct format, or return None.
    """
    # pylint: disable=too-many-branches

    if not _ST_MIN <= sentence_type <= _ST_MAX:
        # The sentence_type is unknown
        return None

    param_types = _SENTENCE_PARAMS[sentence_type]

    if len(param_types) != len(data):
        # The expected number does not match the number of data items
        return None

    params = []
    try:
        for i, dti in enumerate(data):
            pti = param_types[i]
            len_dti = len(dti)
            nothing = dti is None or len_dti == 0
            if pti == "c":
                # A single character
                if len_dti != 1:
                    return None
                params.append(dti)
            elif pti == "C":
                # A single character or Nothing
                if nothing:
                    params.append(None)
                elif len_dti != 1:
                    return None
                else:
                    params.append(dti)
            elif pti == "d":
                # A number parseable as degrees
                params.append(_parse_degrees(dti))
            elif pti == "D":
                # A number parseable as degrees or Nothing
                if nothing:
                    params.append(None)
                else:
                    params.append(_parse_degrees(dti))
            elif pti == "f":
                # A floating point number
                params.append(_parse_float(dti))
            elif pti == "i":
                # An integer
                params.append(_parse_int(dti))
            elif pti == "I":
                # An integer or Nothing
                if nothing:
                    params.append(None)
                else:
                    params.append(_parse_int(dti))
            elif pti == "s":
                # A string
                params.append(dti)
            elif pti == "S":
                # A string or Nothing
                if nothing:
                    params.append(None)
                else:
                    params.append(dti)
            else:
                raise TypeError(f"GPS: Unexpected parameter type '{pti}'")
    except ValueError:
        # Something didn't parse, abort
        return None

    # Return the parsed data
    return params


def _parse_int(nmea_data):
    if nmea_data is None or nmea_data == "":
        return None
    return int(nmea_data)


def _parse_float(nmea_data):
    if nmea_data is None or nmea_data == "":
        return None
    return float(nmea_data)


def _parse_str(nmea_data):
    if nmea_data is None or nmea_data == "":
        return None
    return str(nmea_data)


def _read_degrees(data, index, neg):
    x = data[index]
    if data[index + 1].lower() == neg:
        # prepend a minus sign 
        x = -1.0*x
    return x



class parseNMEA():

    def __init__(self):

        self.latitude = None
        self.longitude = None
        self.acc = 1.0
        self.alt = 1.0

        self.has_fix = False


    def parse_msg(self,msg):
        ff = 'FAIL'
        ss = 'SUCCESS'
        try:
            msgtxt = msg.decode("UTF-8")
        except:
            return ff

        

        sentence = msgtxt.strip().strip('\n')

        if sentence is None or sentence == b"" or len(sentence) < 1:
            return ff

        #try:
        #    sentence = str(sentence, "ascii").strip()
        #except:
        #    return ff

        # Look for a checksum and validate it if present.
        if len(sentence) > 7 and sentence[-3] == "*":
            # Get included checksum, then calculate it and compare.
            expected = int(sentence[-2:], 16)
            actual = 0
            for i in range(1, len(sentence) - 3):
                actual ^= ord(sentence[i])
            if actual != expected:
                return ff# Failed to validate checksum.


        # Remove checksum once validated.
        sentence = sentence[:-3]
        #return sentence
        # Parse out the type of sentence (first string after $ up to comma)
        # and then grab the rest as data within the sentence.
        delimiter = sentence.find(",")
        if delimiter == -1:
            return ff  # Invalid sentence, no comma after data type.
        data_type = sentence[1:delimiter]
        args = sentence[delimiter + 1 :]
        #data_type, args = sentence
        if len(data_type) < 5:
            return ff
        #return sentence
        data_type = bytes(data_type.upper(), "ascii")

        (talker, sentence_type) =  (data_type[:2], data_type[2:])
        args = args.split(",")
        if sentence_type == b"GLL":  # Geographic position - Latitude/Longitude
            return "GLL"
            result = self._parse_gll(args)
            return ss
        elif sentence_type == b"RMC":  # Minimum location info
            result = self._parse_rmc(args)
            return ss
        elif sentence_type == b"GGA":  # 3D location fix
            return "GGA"
            result = self._parse_gga(args)
            return ss
        elif sentence_type == b"GSV":  # Satellites in view
            return "GSV"
            result = self._parse_gsv(args)
            return ss
        elif sentence_type == b"GSA":  # GPS DOP and active satellites
            result = self._parse_gsa(args)
            return result

    
        # At this point we don't have a valid sentence
        return ff

    def _parse_gll(self, data):
        # GLL - Geographic Position - Latitude/Longitude

        if data is None or len(data) != 7:
            return False  # Unexpected number of params.
        data = _parse_data(_GLL, data)
        if data is None:
            return False  # Params didn't parse

        # Latitude
        self.latitude = _read_degrees(data, 0, "s")

        # Longitude
        self.longitude = _read_degrees(data, 2, "w")

        # Status Valid(A) or Invalid(V)
        self.isactivedata = data[5]


        return True

    def _parse_rmc(self, data):
        # RMC - Recommended Minimum Navigation Information

        if data is None or len(data) != 12:
            return False  # Unexpected number of params.
        data = _parse_data(_RMC, data)
        if data is None:
            return False  # Params didn't parse

        # Status Valid(A) or Invalid(V)
        self.isactivedata = data[1]
        if data[1].lower() == "a":
            self.has_fix = 1

        # Latitude
        self.latitude= _read_degrees(data, 2, "s")

        # Longitude
        self.longitude= _read_degrees(data, 4, "w")


        return True

    def _parse_gga(self, data):
        # GGA - Global Positioning System Fix Data

        if data is None or len(data) != 14:
            return False  # Unexpected number of params.
        data = _parse_data(_GGA, data)
        if data is None:
            return False  # Params didn't parse


        # Latitude
        self.latitude= _read_degrees(data, 1, "s")

        # Longitude
        self.longitude= _read_degrees(data, 3, "w")

        # GPS quality indicator
        # 0 - fix not available,
        # 1 - GPS fix,
        # 2 - Differential GPS fix (values above 2 are 2.3 features)
        # 3 - PPS fix
        # 4 - Real Time Kinematic
        # 5 - Float RTK
        # 6 - estimated (dead reckoning)
        # 7 - Manual input mode
        # 8 - Simulation mode
        self.fix_quality = data[5]

        # Number of satellites in use, 0 - 12
        self.satellites = data[6]

        # Horizontal dilution of precision
        self.acc = data[7]

        # Antenna altitude relative to mean sea level
        self.alt = _parse_float(data[8])

        return True

    def _parse_gsa(self, data):
        # GSA - GPS DOP and active satellites

        if data is None or len(data) != 17:
            return False  # Unexpected number of params.
        data = _parse_data(_GSA, data)



        if data is None:
            return False  # Params didn't parse


        # HDOP, horizontal dilution of precision
        self.acc = _parse_float(data[15])



        return True

    def _parse_gsv(self, data):
        # GSV - Satellites in view
        # pylint: disable=too-many-branches

        if data is None or len(data) not in (7, 11, 15, 19):
            return False  # Unexpected number of params.
        data = _parse_data(
            {7: _GSV7, 11: _GSV11, 15: _GSV15, 19: _GSV19}[len(data)],
            data,
        )
        if data is None:
            return False  # Params didn't parse

        # Number of satellites in view
        self.satellites = data[2]

        return True

