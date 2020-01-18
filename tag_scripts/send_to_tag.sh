#!/bin/bash
# Script for sending code to mataki tags
#
# Steps for using:
# 1. Connect mataki tag via support board and usb port
# 2. Connect to serial comm with screen: screen /dev/ttyUSB0 115200
# 3. Switch on tag with support board switch SW2
# 4. Hit C on screen console to prevent script start-up
# 5. Disconnect from screen ctrl+a+k
# 6. Run this script, usage: ./send_to_tag.sh file
# -----------------------------------------------------------------------------

filename=$1

savename="${filename%.*}"

stty -F /dev/ttyUSB0 115200 raw -echo -echoe -echok -echoctl -echoke

# send NEW command to clear the current script
echo -n -e "NEW\r"  >> /dev/ttyUSB0

# loop over the file and send new script line by line
while read -r line
do
  echo -n -e "$line\r" >> /dev/ttyUSB0 
  #echo -e "$line\r" 
  sleep 0.1
done < "$filename"

# send the SAVE command to write to flash memory
echo -n -e "SAVE \"$savename\"\r"  >> /dev/ttyUSB0
