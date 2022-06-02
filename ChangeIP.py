#!/usr/bin/env python

import os
import logging
import subprocess
# import netifaces as ni

NET_DIR='/sys/class/net'

# NEW_IP only used when running this file's main function
NEW_IP='192.168.1.240'

def changeStaticIP(new_ip, force=False):
    # If the force parameter is set to True, refreshIP() will be run whether the new ip matches the dhcpcd.conf file or not

    conf_file = '/etc/dhcpcd.conf'
    try:
        ip_value_changed = False
        # Sanitize/validate params above
        with open(conf_file, 'r') as file:
            data = file.readlines()

        # Find if config exists
        ethFound = next((x for x in data if 'interface eth0' in x), None)

        if ethFound:
            ethIndex = data.index(ethFound)
            if data[ethIndex].startswith('#'):
                data[ethIndex].replace('#', '') # commented out by default, make active
                ip_value_changed = True

        # If config is found, use index to edit the lines you need ( the next 3)
        if ethIndex:
            if data[ethIndex+1] != f'static ip_address={new_ip}/24':  
                data[ethIndex+1] = f'static ip_address={new_ip}/24'
                ip_value_changed = True
                
            with open(conf_file, 'w') as file:
                file.writelines( data )

    except Exception as ex:
        logging.exception("IP changing error: %s", ex)
    finally:
        if (ip_value_changed or force):
            refreshIP()
        pass
        
def refreshIP():

    subprocess.call(['sudo','systemctl','daemon-reload'])
    subprocess.call(['sudo','systemctl','stop','dhcpcd.service'])

    for net_dev in os.listdir(NET_DIR):

        subprocess.call(['sudo','ip','addr','flush','dev',net_dev])

    subprocess.call(['sudo','systemctl','start','dhcpcd.service'])
    subprocess.call(['sudo','systemctl','restart','networking.service'])

def main():

    
    changeStaticIP(NEW_IP)
    

    print("done")
    

if __name__ == '__main__':
    main()