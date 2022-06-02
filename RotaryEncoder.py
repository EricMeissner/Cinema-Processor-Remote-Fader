#!/usr/bin/env python3

#Modified from https://github.com/mivallion/Encoder
 
import signal                   
import RPi.GPIO as GPIO
import time

#Rotary encoder and cp750 controller initialization
class RotaryEncoder():
    def __init__(self, A, B):
        #Set up Rotary Encoder GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.A = A
        self.B = B
        self.pos = 0                    # How many ticks turned since last update)
        self.state = 0                  # 4 flags checking the current and previous state of the rotary encoder
        if GPIO.input(A):
            self.state |= 1
        if GPIO.input(B):
            self.state |= 2
        GPIO.add_event_detect(A, GPIO.BOTH, callback=self.__update)
        GPIO.add_event_detect(B, GPIO.BOTH, callback=self.__update)
    
    """
    update() calling every time when value on A or B pins changes.
    It updates the pos based on previous and current states
    of the rotary encoder.
    """
    def __update(self, channel): 
        state = self.state & 3
        if GPIO.input(self.A):
            state |= 4
        if GPIO.input(self.B):
            state |= 8

        self.state = state >> 2

        if state == 1 or state == 7 or state == 8 or state == 14:
            self.pos += 1
        elif state == 2 or state == 4 or state == 11 or state == 13:
            self.pos -= 1
        elif state == 3 or state == 12:
            self.pos += 2
        elif state == 6 or state == 9:
            self.pos -= 2


    