#!/usr/bin/env python3
#This class deals with communicating with the CP850/950

#Modified significantly from https://github.com/Cybso/cp750client

import socket
import CinemaProcessor
import logging

# Only used for main() at time of writing this comment
import Config
import time

LOGGER = logging.getLogger(__name__)
ERROR_PREFIX='⚠'
PORT = Config.DOLBYPORT


def error_to_str(e):
    """ Converts an Exception to string """
    if hasattr(e, 'message') and e.message is not None:
        return ERROR_PREFIX + e.message
    if hasattr(e, 'strerror') and e.strerror is not None:
        return ERROR_PREFIX + e.strerror
    return ERROR_PREFIX + type(e).__name__LOGGER

class JSD60Control(CinemaProcessor.CinemaProcessor):
    def __init__(self, host):
        super().__init__(host, PORT)
    
    def getState(self):
        if self.socket is None:
            return "disconnected"
        else:
            # Test if socket is alive...
            LOGGER.debug('Testing if socket is alive')
            result = self.send('jsd60.sys.fader')
                
            if not result or result.startswith(ERROR_PREFIX):
                self.disconnect()
                return result
            return "connected"
    
    def connect(self):
        if self.socket is not None:
            self.disconnect()
        LOGGER.debug("Connecting to %s:%d" % (self.destination, self.port))
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.destination, self.port))
            s.settimeout(500)
#             s.setblocking(False)
#             self.stream = s.makefile("rwb", 0)
            self.socket = s
        except Exception as e:
            LOGGER.exception("Failed to connect to %s:%d" % (self.destination, self.port))
            
            return error_to_str(e)
        return self.getState()
    
    def disconnect(self):
        if self.socket is not None:
            LOGGER.debug("Disconnecting from %s:%d" % (self.destination, self.port))
            try:
                self.socket.close()
            except  Exception as e:
                LOGGER.exception("Failed to close connection")
                return error_to_str(e)
            finally:
                self.socket = None
#                 self.stream = None
        return self.getState()
    
    def send(self, command):
        LOGGER.debug("Command: %s" % command)
        if self.socket is None:
            self.connect()
            if self.socket is None:
                LOGGER.warn("Socket is disconnected")
                return self.getStatestripvalue()

        try:
            self.socket.sendall(command.encode('UTF-8') + b"\r\n")
            result = self.socket.recv(1024).decode('UTF-8').strip()
            LOGGER.debug(f'Response: {result}')
            return result
        except Exception as e:
            LOGGER.exception("Command '%s' failed" % command)
            if e.errno == errno.EWOULDBLOCK:
                LOGGER.info("errno.EWOULDBLOCK found______________________")
                pass
            else:
                return error_to_str(e)
    
    
    # Extracts the actual value from the response from the Cinema processor
    # JSD60 just returns a value, not response text.
    def stripvalue(self, responseText):
        value = responseText
        if (value.isdigit()):
            return int(value)
        else:
            return value

    # Adds or subtracts an integer to the fader
#     def addfader(self, value=1):
#        see CinemaProcessor
     
    def getfader(self):
        return self.stripvalue(self.send('jsd60.sys.fader'))
    
    def setfader(self, value):
        return self.stripvalue(self.send(f'jsd60.sys.fader\t{value}'))
    
    def setmute(self, mute=1):
        return self.stripvalue(self.send(f'jsd60.sys.mute\t{mute}'))
    
    def getmute(self):
        return self.stripvalue(self.send('jsd60.sys.mute'))
    
    def displayfader(self):
        rawfader = str(self.getfader())
        formattedfader = rawfader[:-2]+'.'+rawfader[-2:-1] #add decimal point 2 spaces over from the right and drop the 
        return f'{str(formattedfader).rjust(5," ")}'
    
def main():
#     logging.basicConfig(filename='CP850Control.log', encoding='utf-16', level=logging.INFO)
#     LOGGER.info('________STARTING TEST________')
#     print('Note: This won\'t display on the digital display, just the console.')
#     cp = CP850Control(Config.HOST, Config.PORT)
#     cp.connect()
#     while cp.getState() != 'connected':
#         print('Check connection')
#         time.sleep(1)
#         cp.connect()
#     print(cp.getfader())
#     time.sleep(1)
#     cp.addfader(5)
#     print(cp.getfader())
#     time.sleep(1)
#     cp.setfader(50)
#     print(cp.getfader())
#     time.sleep(1)
#     cp.setfader(70)
#     print(cp.getfader())
    pass
    
if __name__ == '__main__':
    main()
