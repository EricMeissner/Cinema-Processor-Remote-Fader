#!/usr/bin/env python3

import time
import math
import board
import busio
from adafruit_ht16k33 import segments
import tm1637
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import logging
from datetime import datetime
from pynput.keyboard import *
from enum import Enum

#Files should be in the same folder as this file.
import CP650Control
import CP750Control
import CP850Control
import JSD60Control
import JSD100Control
import RotaryEncoder
import ChangeIP
import Config

# Switch to debug if you want a lot of unnecessary garbage in your log file when things go weird.
LOGGING_LEVEL = Config.LOGGING_LEVEL

class ProgramState(Enum):
    LOADING = 0
    CONNECTING = 1
    CONNECTED = 2
    EDIT_CPTYPE = 3
    EDIT_CPIP = 4
    EDIT_OWNIP = 5
    RESTART = 6
    ERROR = 7
    SHUTDOWN= 8
    
# Types of Cinema Processors supported.
class CPTypeCode(Enum):
    CP650 = 1
    CP750 = 2
    CP850 = 3
    CP950 = 4
    JSD60 = 5
    JSD100 = 6
# UPDATE THIS WHEN YOU ADD MORE CPTypeCodes!    
LASTCPTYPEVALUE = 6

# Encoder pins
APIN=Config.APIN
BPIN=Config.BPIN

DISPLAYTYPE = Config.DISPLAYTYPE

# Encoder Sensitivity
SENSITIVITY = Config.SENSITIVITY

# Polling rate
delay=Config.POLLING_DELAY

# Absolute filepath to the project folder. 
FILEPATH=Config.FILEPATH

# Cinema Processor
cp = None

# flag is set to tell the loop to terminate the program.
terminate = False

# Tracks user keyboard input for display when in a state where the device accepts input.
keyInput = ""

# If displaying an error to the user on the OLED, this will be used 
errorOutput = ""

# this function is called when a keyboard key is pressed
def press_on(key):
    global cp,terminate,keyInput,pState,cpType,host,ownIP,newCPType
    if key == Key.esc:
        terminate = True
        pState = ProgramState.SHUTDOWN
        refeshOLED()
        return False
    elif key == Key.media_volume_up:
        cp.addfader(1)
    elif key == Key.media_volume_down:
        cp.addfader(-1)
    elif key == Key.f1 and pState in (ProgramState.CONNECTING, ProgramState.CONNECTED, ProgramState.ERROR):
        pState = ProgramState.EDIT_CPTYPE
        newCPType = cpType
        refeshOLED()
    elif key == Key.enter and pState in (ProgramState.EDIT_CPTYPE, ProgramState.EDIT_CPIP, ProgramState.EDIT_OWNIP):
        if pState == ProgramState.EDIT_CPTYPE:
            cpType = newCPType
            newCPType = None
            pState = ProgramState.EDIT_CPIP
            keyInput = host
        elif pState == ProgramState.EDIT_CPIP:
            # TODO: Validation
            host = keyInput.strip()
            pState = ProgramState.EDIT_OWNIP
            keyInput = ownIP
        elif pState == ProgramState.EDIT_OWNIP:
            # TODO: Validation
            ownIP = keyInput.strip()
            saveData()
            pState = ProgramState.RESTART
            keyInput = ""
        refeshOLED()
    elif key in (Key.up, Key.down) and pState == ProgramState.EDIT_CPTYPE:
        if (key == Key.down): 
            if (newCPType.value <= 1):
                newCPType = CPTypeCode(LASTCPTYPEVALUE)
            else:
                newCPType = CPTypeCode(newCPType.value-1)
        elif (key == Key.up):
            if (newCPType.value >= LASTCPTYPEVALUE):
                newCPType = CPTypeCode(1)
            else:
                newCPType = CPTypeCode(newCPType.value+1)
        refeshOLED()
    elif key == Key.backspace and pState in (ProgramState.EDIT_CPIP, ProgramState.EDIT_OWNIP):
        if len(keyInput) > 0:
            keyInput = keyInput[:-1]
            refeshOLED()

    else:
        if hasattr(key, "char") and pState in (ProgramState.EDIT_CPIP, ProgramState.EDIT_OWNIP):
            #TODO: Only allow numeric and "." inputs
            keyInput = keyInput + key.char
            refeshOLED()

            
# This function is called when a key is released.   
def press_off(key):
    pass
    
# Set up the keyboard listener to run press_on when a key is pressed.
def setUpKeyboard():
    Listener(on_press = press_on, on_release = press_off).start()

# Extract saved data from data.txt
def getData():
    global ownIP,host,cpType
    try:
        with open(f'{FILEPATH}/data.txt', 'r') as file:
            data = file.readlines()

        # Scan data file line by line
        for x in data:
            #determine if the line is defining a variable and what variable it is.
            #Split the line by whitespace, take the second text string (the value), and remove any quotes
            #TODO: Basic validation
            if x.startswith('ownIP:'):
                ownIP = x.split()[1].replace("'","").replace('"','')
            elif x.startswith('cpIP:'):
                host = x.split()[1].replace("'","").replace('"','')
            elif x.startswith('cpType:'):
                cpType = CPTypeCode[x.split()[1].replace("'","").replace('"','').upper()]

    except Exception as ex:
        logging.exception("File read error: %s", ex)

# Save settings data to data.txt 
def saveData():
    global ownIP,host,cpType
    try:
   
        with open(f'{FILEPATH}/data.txt', 'w') as file:

            file.write(f'ownIP: {ownIP}\n')
            file.write(f'cpIP: {host}\n')
            file.write(f'cpType: {cpType.name}\n')

    except Exception as ex:
        logging.exception("Data save error: %s", ex)

# Sets up the 7 segment display.
def setUp7Seg():
    global adafruit_7seg,tm1637_7seg
    
    if(DISPLAYTYPE == 1):
        # Create the I2C interface.
        i2c = busio.I2C(board.SCL, board.SDA)

        # Create the LED segment class.
        # This creates a 157 segment 4 character display:
        adafruit_7seg = segments.Seg7x4(i2c)

        # Clear the display.
        adafruit_7seg.fill(0)
    elif(Config.DISPLAYTYPE == 2):
        tm1637_7seg = tm1637.TM1637(clk=Config.CLK, dio=Config.DIO)
        tm1637_7seg.brightness(0) 

def print7seg(data):
    global adafruit_7seg,tm1637_7seg
    
    if(DISPLAYTYPE == 1):
        adafruit_7seg.print(data)
    elif(Config.DISPLAYTYPE == 2):
        data = data.replace(".","")
        tm1637_7seg.show(data)

# Sets up the OLED display.
def setUpOLED():
    global displayOLED
    # Create the I2C interface.
    i2c = busio.I2C(board.SCL, board.SDA)

    # Create the SSD1306 OLED class.
    # The first two parameters are the pixel width and pixel height.  Change these
    # to the right size for your display!
    displayOLED = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

    # Clear display.
    displayOLED.fill(0)
    displayOLED.show()
    refeshOLED()

# Update the OLED display with what the current state of the program is.
# After you change the program state or any of the displayed variables on the OLEd
# you'll need to call this to update the OLED to show the changes.
def refeshOLED():
    global displayOLED, pState, errorOutput, newCPType
    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    width = displayOLED.width
    height = displayOLED.height
    image = Image.new("1", (width, height)) # 1-bit color image to write on.

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Draw some shapes.
    # First define some constants to allow easy resizing of shapes.
    padding = -2
    top = padding
    bottom = height - padding
    # Move left to right keeping track of the current x position for drawing shapes.
    x = 0

    # Load default font.
    font = ImageFont.load_default()
    
    # Construct the input/message line at the bottom of the OLED display based on program state
    inputLine = ""
    if pState == ProgramState.LOADING:
        inputLine = "LOADING..."
    elif pState == ProgramState.CONNECTING:
        inputLine = "CONNECTING..."
    elif pState == ProgramState.CONNECTED:
        inputLine = f"CONNECTED TO {cpType.name}"
    elif pState == ProgramState.EDIT_CPTYPE:
        inputLine = f"CP TYPE?  {newCPType.name}"
    elif pState == ProgramState.EDIT_CPIP:
        inputLine = f"CPIP? {keyInput}"
    elif pState == ProgramState.EDIT_OWNIP:
        inputLine = f"OWNIP?{keyInput}"
    elif pState == ProgramState.RESTART:
        inputLine = "RESTARTING..."
    elif pState == ProgramState.ERROR:
        if len(errorOutput):
            inputLine = errorOutput.upper()
        else:
            inputLine = "ERROR"
    elif pState == ProgramState.SHUTDOWN:
        inputLine = "SHUTTING DOWN"
    else:
        inputLine = "PROGRAM STATE UNKNOWN"
        
    # Construct the display text.
    draw.text((x, top + 0), f"CP TYPE: {cpType.name}", font=font, fill=255)
    draw.text((x, top + 8), f"CPIP: {host}", font=font, fill=255)
    draw.text((x, top + 16),f"OWNIP:{ownIP}", font=font, fill=255)
    draw.text((x, top + 25),inputLine , font=font, fill=255)
    
    displayOLED.image(image)
    displayOLED.show()

def constructCinemaProcessorObject():
    global cp
    if(cp is not None):
        if(cp.getState() == "connected"):
            cp.disconnect()
        cp = None
    if(cpType == CPTypeCode.CP650):
        cp = CP650Control.CP650Control(host)
    elif(cpType == CPTypeCode.CP750):
        cp = CP750Control.CP750Control(host)
    elif(cpType in [CPTypeCode.CP850, CPTypeCode.CP950]):
        cp = CP850Control.CP850Control(host)
    elif(cpType == CPTypeCode.JSD60):
        cp = JSD60Control.JSD60Control(host)
    elif(cpType == CPTypeCode.JSD100):
        cp = JSD100Control.JSD100Control(host)
    else:
        logging.error('Invalid cinema processor type (CPTYPE), check config. defaulting to CP850/CP950')
        cp = CP850Control.CP850Control(host)
    

def setUpCinemaProcessor():
    global cp, pState, display7seg
    constructCinemaProcessorObject()
    pState = ProgramState.CONNECTING
    refeshOLED()
    
    cp.connect()
    
    #Check to see if the Cinema Processor is connected and if it isn't, keep trying each 1 second
    while cp.getState() != 'connected':
        
        #Checks to see if the program has been manually terminated
        if terminate:
            return
        
        print('Check connection                               ',end='\r')
        time.sleep(1) #Consider making this configurable?
        if(pState == ProgramState.RESTART):
            ChangeIP.changeStaticIP(ownIP)
            constructCinemaProcessorObject()
            pState = ProgramState.CONNECTING
            refeshOLED()
        cp.connect()
    pState = ProgramState.CONNECTED
    refeshOLED()
    return
    
def main():
    global cp, pState
    pState = ProgramState.LOADING
    
    # Set up logging
    logging.basicConfig(filename=f'{FILEPATH}/logs/VolumeControl.log', encoding='utf-16', level=LOGGING_LEVEL)
    logging.info(f'_______Starting VolumeControl at {datetime.now().strftime("%m/%d/%Y, %H:%M:%S____________________")}')
    
    # Load settings from data.txt
    getData()
    # Initialize displays, cp,and encoder
    setUp7Seg()
    setUpOLED()
    setUpKeyboard()
    print7seg("-   ")
    
    ChangeIP.changeStaticIP(ownIP)
    print7seg("--  ")
    
    print("Connecting to Cinema Processor")
    setUpCinemaProcessor()
    print7seg("--- ")
    
    if not terminate:
        enc = RotaryEncoder.RotaryEncoder(APIN,BPIN)
        print7seg("----")

    
    while not terminate:
        if (pState == ProgramState.RESTART):
            ChangeIP.changeStaticIP(ownIP)
            setUpCinemaProcessor()
            
        # If the position of the encoder changed, add/subtract it from the fader (modified by sensitivity)
        # Then adjust the position tracking value accordingly (used to be set back to zero, but
        # the sensitivity value would risk dropping half-ticks and the like.
        volumeChange = math.floor(enc.pos*SENSITIVITY)
        if(volumeChange):
            if(cp.addfader(volumeChange)):          #Send the volume change and check to see if it went through correctly
                enc.pos = enc.pos - (volumeChange/SENSITIVITY)
            else:
                enc.pos = 0                         #Swallow any volume changes during connection difficulty
                
        #Update the display with the current value
        currentFader = cp.displayfader()
        if(currentFader):
            print(currentFader+'                       ',end='\r') #Prints to the console
            print7seg(currentFader) #Prints the volume to the 7 segment display
            
        else:
            print('Connection Issue                       ',end='\r')
            print7seg('E   ') 
            setUpCinemaProcessor()              #Disconnect and reconnect socket.
        time.sleep(delay)
        
    # When the program is terminated, disconnect from the Cinema Processor and clear the displays.
    cp.disconnect()
    print7seg("    ")
    displayOLED.fill(0)
    displayOLED.show()
    

if __name__ == '__main__':
    main()
