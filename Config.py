# Configuration file, seldom needs to be changed.

import logging
# LOGGING_LEVEL = logging.DEBUG
LOGGING_LEVEL = logging.INFO
# Absolute path to directory holding this application's files
FILEPATH = "/home/pi/FTP/VolumeControl"

# Polling/update delay in seconds
# A lower delay will make the the fader more responsive, BUT if it is too low
# the frequent requests to the Cinema Processor can be rejected, causing buggy responses.
POLLING_DELAY = 0.1

# Encoder Sensitivity
# We had an encoder that incremented twice for one click, so we added this so we could
# decrease the sensitivity to 0.5 for it.
SENSITIVITY = 1

# Encoder pins
# The pins that the rotary encoder (the knob) is connected to.
# Unless you are rewiring the device pi, you should not need to touch this.
# If turning the knob is making the volume go the opposite way, swap these numbers.
APIN=12
BPIN=16

# 7 segmeny display type
# 1 = i2c Adafruit HT16K33 segments
# 2 = TM1637
DISPLAYTYPE = 1

# TM1637 data pins (only necessary if display type is TM1637, ignored if TM1637 not used)
CLK = 5
DIO = 4

# Ports for Cinema Processors
# These shouldn't ever need to change
# DOLBYPORT = 61408       # port for Dolby CP_50 Cinema Processors
# JSDPORT = 10001         # port for JSD Cinema Processors
