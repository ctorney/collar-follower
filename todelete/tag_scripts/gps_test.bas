10   REM ===== TEST GPS =====
20    _LED = 0
25   _DBGGPS=1
30    _GPS = 1
40   IF _FIXVALID = 1 THEN _LED = 1 : PRINT TIME$ ; " Lat:"; _FIXLAT ;" Long:"; _FIXLON ;" Alt:"; _FIXALT ;" HDOP:"; _FIXHDOP;" SATS:"; _FIXSATS
60   GOTO 30
