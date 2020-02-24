10   REM =================================================
20   REM ===     Sender script for for Mataki-Lite     ===
30   REM ===      Wakes up and switches to high        ===
40   REM ===           frequency GPS fixes             ===
50   REM =================================================
60     PRINT
70     PRINT "Mataki-Lite Sender Tag Script V1.0"
90     PRINT
100  REM *** GPS Tracking Settings ***
110    firstfixtime = 4 * 60 
150  REM *** Radio Settings ***
160    radiointerval = 3 * 60 : REM 3 mins between base contact attempts
165    radiosearchtime = 120 : REM 2 mins searching 
180    PRINT "Base Radio interval : "; radiointerval / 60 ;" minutes"
190  REM *** Startup state ***
200    REM _LED = 0
210    REM _GPS = -1
220    _DBGGPS=1
250    sleeptime = 10
270    waittime = 3 * 60
299    GOSUB 1000 : REM always turn radio on after start-up
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
1080   IF r$ = "M_PING" THEN stopsearchtime = CLOCK + waittime : GOSUB 3000
1090   IF B_MODE = 1 THEN GOSUB 2000
1100   UNTIL CLOCK > stopsearchtime
1110   _RADIO = 0
1120   _GPS = -1
1130   _LED = 0
1150   RETURN
2000   REM ENTERING BROADCAST MODE
2010   _LED = 0
2020   _RADIO = 0
2021   endtime = CLOCK + firstfixtime
2022   REPEAT
2030   t1 = CLOCK
2040   _GPS = 2
2050   t2 = CLOCK
2052   if (t2 - t1) < 10 THEN GOTO 2061
2055   endtime = t2 + (endtime - t1)
2060   stopsearchtime = t2 + (stopsearchtime - t1)
2061   UNTIL _FIXVALID OR (CLOCK > endtime)
2062   IF _FIXVALID = 0 THEN GOSUB 4000 : _RESET = 1 
2065   LAT$ = STR$(FIX(_FIXLAT)) + MID$(STR$(ABS(_FIXLAT-FIX(_FIXLAT))),2,7) : REM build string separately to ensure 6 digits precision
2066   LON$ = STR$(FIX(_FIXLON)) + MID$(STR$(ABS(_FIXLON-FIX(_FIXLON))),2,7) : REM build string separately to ensure 6 digits precision
2070   MSG$ = "FIX," + STR$(_ID) + "," + STR$(_FIXVALID) + "," + LAT$  + "," + LON$ + "," + STR$(_FIXHDOP) + "," + STR$(_FIXSATS) + "," + STR$(_Vbatt)
2080   REM SEND TO BASE
2090   _RADTXPWR = 10
2100   _RADIO = 2
2110   _RADMSG$ = MSG$
2120   DELAY 2
2130   RETURN
2999   REM code to send a msg to receiver on entering broadcast mode
3000   IF B_MODE = 0 THEN GOSUB 3030
3010   B_MODE = 1
3020   RETURN
3030   MSG$ =  STR$(_ID) + " ENTERING BROADCAST MODE"
3040   _RADTXPWR = 10
3050   _RADIO = 2
3060   _RADMSG$ = MSG$
3070   RETURN
3999   REM code to send a msg to receiver on entering broadcast mode
4000   MSG$ =  STR$(_ID) + " COULDN'T GET A GPS FIX. REBOOTING..."
4010   _RADTXPWR = 10
4020   _RADIO = 2
4030   _RADMSG$ = MSG$
4040   RETURN
