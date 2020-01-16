10   REM =================================================
20   REM ===     Sender script for for Mataki-Lite     ===
30   REM ===      Wakes up and switches to high        ===
40   REM ===           frequency GPS fixes             ===
50   REM =================================================
60     PRINT
70     PRINT "Mataki-Lite Sender Tag Script V1.0"
90     PRINT
100  REM *** GPS Tracking Settings ***
110    fixinterval = 10 * 60       : REM 10 mins between fixes
120    firstfixsearchtime = 4 * 60 : REM Leave GPS on for max. 4 mins to get first fix
130    fixsearchtime = 30          : REM Leave GPS on for max. 30 secs to get subsequent fixes
140    gpsmode = 1                 : REM Automatic mode: Get a fix and log it
150  REM *** Radio Settings ***
160    radiointerval = 30 * 60 : REM 30 mins between base contact attempts
170    PRINT "GPS Fix interval    : "; fixinterval / 60 ;" minutes"
180    PRINT "Base Radio interval : "; radiointerval / 60 ;" minutes"
190  REM *** Startup state ***
200    _LED = 0
210    _GPS = 0
220    fixes = 0
230    fixtime = CLOCK + fixinterval
240    radiotime = CLOCK + radiointerval
250    sleeptime = 10
260    radioled = 1
299  REM *** Main Loop ***
300    IF CLOCK >= fixtime THEN GOSUB 1000
310    IF CLOCK >= radiotime THEN GOSUB 2000
320  REM *** Enter low power mode for a maximum of <sleeptime> seconds ***
330    _SLEEP = sleeptime
360    GOTO 300
999  REM *** Try to get a GPS Fix ****
1000   PRINT TIME$ ;" GPS On"
1020   IF fixes = 0 GOSUB 1200 ELSE GOSUB 1400
1100   _GPS = 0
1110   IF _FIXVALID = 0 THEN 1120
1112   PRINT "Lat:"; _FIXLAT ;" Long:"; _FIXLON ;" Alt:"; _FIXALT ;" HDOP:"; _FIXHDOP;" SATS:"; _FIXSATS
1115   fixes = fixes + 1
1118   PRINT fixes ;" fixes"
1120   PRINT TIME$ ;" GPS Off"
1130   PRINT "Log Used = "; _logused ;"/"; _logcap ;" entries ("; ROUND((_logused * 100) / _logcap) ;"%)"
1140   PRINT "Battery "; _Vbatt ;"V"
1150   PRINT TIME$ ;" Next fix in "; fixinterval / 60 ;" minutes"
1160   fixtime = CLOCK + fixinterval
1190   RETURN
1199 REM *** First Fix - CLOCK value will jump when GPS time is set ***
1200   endtime = CLOCK + firstfixsearchtime
1210   REPEAT
1220     t1 = CLOCK
1230     _GPS = gpsmode
1240     t2 = CLOCK
1250     if (t2 - t1) < 10 THEN GOTO 1300
1260       REM GPS Time has reset CLOCK - update all the timer values depending on it
1270       endtime = t2 + (endtime - t1)
1280       fixtime = t2 + (fixtime - t1)
1290       radiotime = t2 + (radiotime - t1)
1300   UNTIL _FIXVALID OR (CLOCK > endtime)
1310   RETURN
1399 REM *** Normal Fix - We should be able to rely on CLOCK value now ***
1400   endtime = CLOCK + fixsearchtime
1410   REPEAT
1430     _GPS = gpsmode
1460   UNTIL _FIXVALID OR (CLOCK > endtime)
1500   RETURN
1999 REM *** Radio ****
2000   IF _LOGUSED = 0 THEN PRINT "No logs to send to base station" : GOTO 2100
2010   PRINT COLOR(6); "Trying to contact base station"; COLOR(0)
2020   _RADIO = 1
2025   d = 1
2030 REM Wait with the radio on until we timeout - if contact is made, we will be re-booted
2040   REPEAT
2050     DELAY 0.01
2060     IF (d MOD 200) = 0 THEN _LED = radioled
2070     IF (d MOD 200) = 5 THEN _LED = 0
2080     d = d + 1
2085   UNTIL _CONTACT = 0
2086 REM Either no contact or the radio transaction was incomplete
2090   _RADIO = 0
2100   _LED = 0
2110   PRINT TIME$ ;" Next radio in "; radiointerval / 60 ;" minutes"
2150   radiotime = CLOCK + radiointerval
2190   RETURN
