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
logging.basicConfig(filename = join(HOMEPATH, "nanny.log"), 
                    mode='a',  
                    level=logging.INFO,
                    format='%(asctime)s %(message)s')

TRIGGERS = ['stratum connection error',
            'killed']

EXPECTED_HASHRATE = 160000000

def triggered(lines):
    """Checks if any of the trigger words are found in any of the lines"""
    for line in reversed(lines):
        tl = [trigger for trigger in TRIGGERS if trigger in line.lower()]
    
    if tl: return tl[0]
    else:  return False
    
def avg_hashrate(lines, n):
    """Calculates the average hashrate based on the n last 
    hashing attempts"""
    pass

def stuck(lines, limit = 3):
    """
    Check if the miner is stuck on submitting solution.
    
    returns True if the miner is stuck
    """
    c=0
    for line in reversed(lines):
            if "Solution found; Submitting ..." in line:
                c += 1
            if "Worker stopping" in line:
                return False
            #Reset counter
            #if 3 "soulution found" is found before "worker stopping"
            #the miner can be considered dead
            if c > limit:
                return True

def reboot(message):
    """Reboots the miner and logs the message"""
    logging.info(message)
    system("/sbin/reboot")

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
        
        #Check if the miner is stuck on submitting solution
        if stuck(lines):
            reboot("Stuck on Submitting solution... rebooting, hangon!")
            
        #Check other lines that should trigger a reboot
        if triggered(lines):
            reboot("Reboot triggered: %s" % triggered(lines))
        
        #Check if average hashrate is to low (maybe we've lost a gfx-card).
        if avg_hashrate(lines, 10) < EXPECTED_HASHRATE:
            reboot("Avg hashrate below threshold (%d), rebooting!" 
                   % avg_hashrate(lines, 10))
            
        sleep(15)

if __name__ == "__main__":
    main()
