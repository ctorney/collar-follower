10   REM =================================================
20   REM ===    Receiver script for for Mataki-Lite    ===
30   REM === Wakes up sender tags and relays GPS fixes ===
50   REM =================================================
60     PRINT
70     PRINT "Mataki-Lite Receiver Tag Script V1.0"
90     PRINT
100  REM *** GPS Tracking Settings ***
110    pinginterval = 30           : REM 10 mins between fixes
120    listentime  = 30  : REM Leave GPS on for max. 4 mins to get first fix
130    waittime  = 5 * 60  : REM Leave GPS on for max. 5 mins to get first fix
190  REM *** Startup state ***
199  REM *** 2 slow flashes for sender tags ***
200    FOR x = 1 TO 2
201      _LED = 1
202      DELAY 3
203      _LED = 0
204      DELAY 1
205    NEXT
210    _GPS = -1
220    _RADCHAN = 29
230    _RADSPEED = 2
240    _RADTXPWR = 10
1000   _RADIO = 2
1010   PRINT "Sending out a ping.."
1030   endtime = CLOCK + listentime
1040   REPEAT
1050     _RADMSG$ = "PINGPONG"
1055     DELAY 1
1060     r$ = _RADMSG$
1065     IF r$ <> "" THEN PRINT r$
1070     IF r$ = "PONGPING" GOSUB 2000
1060   UNTIL CLOCK > endtime
1080   _RADIO = 0
1085   PRINT "No response so having a snooze..."
1090   DELAY pinginterval
1090   GOTO 1000
1999 REM *** There's someone out there ****
2000   _LED = 1
2001   PRINT "wait.. there's someone there.."
2005   quittime = CLOCK + waittime
2010   REPEAT
2020     r$ = _RADMSG$
2030     IF r$ <> "" THEN PRINT r$
2040     IF LEFT$(r$, 3) = "FIX" THEN quittime = CLOCK + waittime
2050     _RADMSG$ = "PINGPONG" 
2060   UNTIL CLOCK > quittime 
2070   _LED = 0
2080   RETURN
