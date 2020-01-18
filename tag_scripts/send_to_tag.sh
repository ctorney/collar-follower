#!/bin/bash
# Simple line count example, using bash
#
# Bash tutorial: http://linuxconfig.org/Bash_scripting_Tutorial#8-2-read-file-into-bash-array
# My scripting link: http://www.macs.hw.ac.uk/~hwloidl/docs/index.html#scripting
#
# Usage: ./line_count.sh file
# -----------------------------------------------------------------------------

# Link filedescriptor 10 with stdin
# remember the name of the input file
filename=$1

extension="${filename##*.}"
savename="${filename%.*}"
echo $savename
echo $filename

echo "NEW"
# echo "NEW" >> /dev/ttyUSB0
cat $filename
# cat $filename >> /dev/ttyUSB0
echo "SAVE $savename"
# echo "SAVE $savename" >> /dev/ttyUSB0


