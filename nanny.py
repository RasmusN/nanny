#!/usr/bin/python
"""
This script tracks the "error log" from qtminer and looks for patterns
that suggests that the mining has stopped. If found, the computer is rebooted.

In order for this to work, the stderr of qtminer has to be set to ~/nanny/error.
> qtminer -<your usual options> 2> ~/nanny/error

Make sure that /sbin/reboot doesn't require sudo:
> sudo chmod u+s /sbin/reboot

Don't forget set this script to start-on-boot
"""
from os import system
from os.path import join
from os.path import expanduser
from time import sleep
import logging

HOME_PATH = expanduser("~")
logging.basicConfig(filename = "nanny.log", mode='a',  level=logging.INFO,
                    format='%(asctime)s %(message)s')
def main():
    running = True
    #Wait for the mining software to start
    sleep(25)
    logging.info("Starting nanny...")
    while running:
        logging.debug("Checking for errors...")
        try: qt_log_file = open(join(HOME_PATH, "nanny/error"), "r")
        except IOError as err: 
            logging.info(err)
            sleep(10)
            continue
        lines = qt_log_file.readlines()
        qt_log_file.close()
        
        c = 0
        for line in reversed(lines):
            if "Solution found; Submitting ..." in line:
                c += 1
            if "Worker stopping" in line:
                c = 0 #Reset counter
            #if 3 "soulution found" is found before "worker stopping"
            #the miner can be considered dead
            if c > 3:
                logging.info("Stuck on Submitting solution... rebooting, hangon!")
                system("/sbin/reboot")
                break
            if "stratum connection error" in line.lower():
                logging.info("Connection error... rebooting, hangon!")
                system("/sbin/reboot")
                break
            if "killed" in line.lower():
                logging.info("killed... rebooting, hangon!")
                system("/sbin/reboot")
                break
        sleep(15)
if __name__ == "__main__":
    main()
