
import serial
with serial.Serial('/dev/ttyUSB0', 115200, timeout=1) as ser:
    print(ser.name)         # check which port was really used
    while True:
        line = ser.readline()
        print(line)
