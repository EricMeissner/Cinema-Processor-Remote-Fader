#!/usr/bin/env python3
#This class deals with communicating with the JSD100

#Modified significantly from https://github.com/Cybso/cp750client

import socket
import JSD60Control
import logging

# Only used for main() at time of writing this comment
import Config
import time

LOGGER = logging.getLogger(__name__)
ERROR_PREFIX='⚠'
PORT = 10001


def error_to_str(e):
    """ Converts an Exception to string """
    if hasattr(e, 'message') and e.message is not None:
        return ERROR_PREFIX + e.message
    if hasattr(e, 'strerror') and e.strerror is not None:
        return ERROR_PREFIX + e.strerror
    return ERROR_PREFIX + type(e).__name__LOGGER

class JSD100Control(JSD60Control.JSD60Control):
    def __init__(self, host):
        super().__init__(host)
        API_PREFIX='jsd100'
        
def main():
    pass
    
if __name__ == '__main__':
    main()
