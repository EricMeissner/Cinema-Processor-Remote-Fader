#!/usr/bin/env python3
# This is an abstract class for Cinema Processors to in

import socket
from abc import ABC, abstractmethod 

class CinemaProcessor(ABC):
    def __init__(self, host, port):
        self.destination = host
        self.port = port
        self.socket = None
    
    @abstractmethod
    def getState(self):
        pass
    
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def disconnect(self):
        pass
        
    @abstractmethod
    def send(self, command):
        pass
    
    # This will probably need to be overridden, but it works for Dolby Cinema processors
    # A response string is split by spaces and the last element (the response data) is returned.
    # If it's an number, it's cast as an integer first.
    def stripvalue(self, responseText):
        value = responseText.strip().split(" ")[-1]
        if (value.isdigit()):
            return int(value)
        else:
            return value
        
    def addfader(self, value=1):
        if(isinstance(value, int)):
            fader = self.getfader() + value
            if(fader<0):
                self.setfader(0)
            elif(fader>100):
                self.setfader(100)
            else:
                self.setfader(fader)
                
    @abstractmethod
    def getfader(self):
        pass
    
    @abstractmethod
    def setfader(self, value):
        pass
    
    @abstractmethod
    def setmute(self, mute=1):
        pass
    
    @abstractmethod
    def getmute(self):
        pass
    
    @abstractmethod
    def displayfader(self):
        pass