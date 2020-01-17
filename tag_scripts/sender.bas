10   REM =================================================
20   REM ===     Sender script for for Mataki-Lite     ===
30   REM ===      Wakes up and switches to high        ===
40   REM ===           frequency GPS fixes             ===
50   REM =================================================
60     PRINT
70     PRINT "Mataki-Lite Sender Tag Script V1.0"
90     PRINT
100  REM *** GPS Tracking Settings ***
110    fixinterval = 1 * 60       : REM 1 min between fixes
130    gpsoff = -1                 : REM Deep GPS sleep
140    gpson  = 2                 : REM Automatic mode: Get a fix and don't log it
150  REM *** Radio Settings ***
160    radiointerval = 60 * 60 : REM 60 mins between base contact attempts
165    radiosearchtime = 120 : REM 30 seconds searching 
170    PRINT "GPS Fix interval    : "; fixinterval / 60 ;" minutes"
180    PRINT "Base Radio interval : "; radiointerval / 60 ;" minutes"
190  REM *** Startup state ***
200    _LED = 0
210    _GPS = gpsoff
250    sleeptime = 10
270    waittime = 3 * 60
280    listentime = 3
299  REM *** Main Loop ***
300    IF MOD(CLOCK,radiointerval) < 2*sleeptime THEN GOSUB 1000
310  REM *** Enter low power mode for a maximum of <sleeptime> seconds ***
320    _SLEEP = sleeptime
360    GOTO 300
999  REM *** Check my messages ****
1000   PRINT TIME$ ;" Radio On"
1005   stopsearchtime = CLOCK + radiosearchtime
1010   _RADCHAN = 29
1020   _RADSPEED = 2
1030   _RADIO = 2
1040   REPEAT
1050   r$ = _RADMSG$
1060   IF r$ == "PINGPONG" THEN GOSUB 2000
1070   UNTIL CLOCK > stopsearchtime
1080   _RADIO = 0
1090   RETURN
1999 REM *** There's someone out there ****
2000   _RADTXPWR = 10
2010   FOR x = 1 TO 10
2020     _RADMSG$ = "PONGPING"
2030     DELAY 1
2040   NEXT
2050    _RADMSG$ = "Hello, I am number " + STR$(_ID) 
2060    DELAY 1
2070    _RADMSG$ = "I've been waiting for you."
2080   _LED = 1
2090   endtime = CLOCK + waittime
2100   REPEAT
2110     t1 = CLOCK
2120     _GPS = gpson
2130     t2 = CLOCK
2140     endtime = t2 + (endtime - t1)
2145     stopsearchtime = t2 + (stopsearchtime - t1)
2150     _RADMSG$ = "FIX," + STR$(_ID) + "," + STR$(_FIXVALID)) + "," + STR$(_FIXLAT) + "," + STR$(_FIXLON) + "," + STR$(_FIXHDOP) + "," + STR$(_FIXSATS) 
2160     recvtime = CLOCK + listentime
2170     REPEAT
2180       r$ = _RADMSG$
2190       IF r$=="OK" THEN endtime = CLOCK + waittime
2200     UNTIL CLOCK > recvtime
2210     DELAY fixinterval-listentime
2220   UNTIL CLOCK > endtime 
2230   _GPS = gpsoff
2240   _LED = 0
2250   RETURN
