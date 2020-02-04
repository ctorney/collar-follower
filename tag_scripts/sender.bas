10   REM =================================================
20   REM ===     Sender script for for Mataki-Lite     ===
30   REM ===      Wakes up and switches to high        ===
40   REM ===           frequency GPS fixes             ===
50   REM =================================================
60     PRINT
70     PRINT "Mataki-Lite Sender Tag Script V1.0"
90     PRINT
100  REM *** GPS Tracking Settings ***
150  REM *** Radio Settings ***
160    radiointerval = 3 * 60 : REM 60 mins between base contact attempts
165    radiosearchtime = 120 : REM 2 mins searching 
180    PRINT "Base Radio interval : "; radiointerval / 60 ;" minutes"
190  REM *** Startup state ***
200    _LED = 0
210    _GPS = -1
250    sleeptime = 10
270    waittime = 3 * 60
299  REM *** Main Loop ***
300    IF CLOCK MOD radiointerval < 2*sleeptime THEN GOSUB 1000
310  REM *** Enter low power mode for a maximum of <sleeptime> seconds ***
315    PRINT STR$(CLOCK MOD radiointerval); "SLEEPING.."
320    _SLEEP = sleeptime
360    GOTO 300
1000   PRINT TIME$ ;" Radio On"
1010   stopsearchtime = CLOCK + radiosearchtime
1020   _RADCHAN = 29
1030   _RADSPEED = 2
1040   _RADIO = 2
1050   B_MODE = 0
1060   REPEAT
1070   r$ = _RADMSG$
1080   IF r$ = "M_PING" THEN stopsearchtime = CLOCK + waittime : B_MODE = 1
1090   IF B_MODE = 1 THEN GOSUB 2000
1100   UNTIL CLOCK > stopsearchtime
1110   _RADIO = 0
1120   _GPS = -1
1130   _LED = 0
1140   PRINT TIME$ ;" All off"
1150   RETURN
2000   PRINT "ENTERING BROADCAST MODE"
2010   _LED = 1
2020   _RADIO = 0
2030   t1 = CLOCK
2040   _GPS = 2
2050   t2 = CLOCK
2060   stopsearchtime = t2 + (stopsearchtime - t1)
2065   LAT$ = STR$(FIX(_FIXLAT)) + MID$(STR$(ABS(_FIXLAT-FIX(_FIXLAT))),2,7) : REM build string separately to ensure 6 digits precision
2066   LON$ = STR$(FIX(_FIXLON)) + MID$(STR$(ABS(_FIXLON-FIX(_FIXLON))),2,7) : REM build string separately to ensure 6 digits precision
2070   MSG$ = "FIX," + STR$(_ID) + "," + STR$(_FIXVALID) + "," + LAT$  + "," + LON$ + "," + STR$(_FIXHDOP) + "," + STR$(_FIXSATS) + "," + STR$(_Vbatt)
2080   PRINT MSG$  
2090   _RADTXPWR = 10
2100   _RADIO = 2
2110   _RADMSG$ = MSG$
2120   DELAY 2
2130   RETURN
