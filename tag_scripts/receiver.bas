10   REM =================================================
20   REM ===    Receiver script for for Mataki-Lite    ===
30   REM === Wakes up sender tags and relays GPS fixes ===
50   REM =================================================
60     PRINT
70     PRINT "Mataki-Lite Receiver Tag Script V1.0"
90     PRINT
100  REM *** Startup state ***
120   _RADCHAN = 29
130   _RADSPEED = 2
140   _RADTXPWR = 10
150   _RADIO = 2
199  REM *** Main loop ***
200   _RADMSG$ = "M_PING"
210   DELAY 0.5
211   _LED = 0
220   r$ = _RADMSG$
230   IF r$ <> "" THEN _LED = 1 : PRINT r$; "," ; TIME$
235   IF _FIXVALID = 0 THEN _GPS = 2 : REM JUST FOR THE TIME TO BE ACCURATE
240   GOTO 200
