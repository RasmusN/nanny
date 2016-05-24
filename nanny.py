#!/usr/bin/python
"""
This script tracks the "error log" from qtminer and looks for patterns
that suggests that the mining has stopped. If found, the computer is rebooted.

In order for this to work, the stderr of qtminer has to be set to ~/nanny/error.
$ qtminer -<your usual options> 2> ~/nanny/error

Make sure that /sbin/reboot doesn't require sudo:
$ sudo chmod u+s /sbin/reboot

Don't forget set this script to start-on-boot
"""

import re
from os import system
from os.path import join
from os.path import expanduser
from time import sleep
import logging

HOME_PATH = expanduser("~")
logging.basicConfig(filename = join(HOME_PATH, "nanny.log"), 
                    mode='a',  
                    level=logging.INFO,
                    format='%(asctime)s %(message)s')

TRIGGERS = ['stratum connection error',
            'killed']

EXPECTED_HASHRATE = 160000000

def disconnected(lines, sample_size = 50, trigger = 20):
    """Checks if the server is disconnected and returns True if so.
    This function will be triggered if the <sample_size> number of
    lines from the bottom of lines contain more than <trigger> of
    'Waiting for work package...'
    
    @rtype: bool"""
    if len(lines) < sample_size:
        return False
    
    c = i = 0
    for line in reversed(lines):
        
        #Break loop if i is bigger than sample size
        if i > sample_size: break
        
        if "Waiting for work package..." in line:
            c += 1
        i += 1
        
    if c >= trigger:
        return True
    else: 
        return False
    
    
def triggered(lines):
    """Checks if any of the trigger words are found in any of the lines"""
    for line in reversed(lines):
        tl = [trigger for trigger in TRIGGERS if trigger in line.lower()]
    
    if tl: return tl[0]
    else:  return False
    
def avg_hashrate(lines, n):
    """Calculates the average hashrate based on the n last 
    hashing attempts
    
    Returnes 'None' if the number of samples is less than n
    
    Typical raw input:
    i  16:31:08|main  Push: New work package received
    i  16:31:08|main  Got work package:
    i  16:31:08|main    Header-hash: f2e7406b47d32377cb681e12b7a5ad3aff7c8e6593f49e47899c89c34bfbd439
    i  16:31:08|main    Seedhash: abad8f99f3918bf903c6a909d9bbc0fdfa5a2f4b9cb1196175ec825c6610126c
    i  16:31:08|main    Target: 0000000112e0be826d694b2e62d01511f12a6061fbaec8bc02357593e70e52ba
    i  16:31:14|main  Mining on PoWhash #f2e7406b : 32505856 H/s = 65011712 hashes / 2 s
    i  16:31:16|main  Mining on PoWhash #f2e7406b : 32360234 H/s = 65011712 hashes / 2.009 s
    i  16:31:18|main  Mining on PoWhash #f2e7406b : 32295932 H/s = 65011712 hashes / 2.013 s
    i  16:31:20|main  Mining on PoWhash #f2e7406b : 31176689 H/s = 62914560 hashes / 2.018 s
    i  16:31:22|main  Mining on PoWhash #f2e7406b : 32279896 H/s = 65011712 hashes / 2.014 s
    i  16:31:24|main  Mining on PoWhash #f2e7406b : 32247873 H/s = 65011712 hashes / 2.016 s
    i  16:31:26|main  Mining on PoWhash #f2e7406b : 32554688 H/s = 65011712 hashes / 1.997 s
    i  16:31:28|main  Mining on PoWhash #f2e7406b : 31285211 H/s = 62914560 hashes / 2.011 s
    """
    hashrates = []
    for line in reversed(lines):
        if "Mining on PoWhash" in line:
            hrs = re.search("\d+ H/s", line).group(0)
            hr = int(hrs.split()[0])
            
            dts = re.search("\d+ s", line).group(0)
            dt = float(dts.split()[0])

            #Smaller samples than 1.8s tend to be unstable
            if dt > 1.8:
                hashrates.append(hr)

            if len(hashrates) >= n:
                break
            
    #If there are less samples than n, return None
    if len(hashrates) < n:
        return None

    return sum(hashrates)/float(len(hashrates))

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
        
        #Read qtminer stderr-file
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
        if (avg_hashrate(lines, 50) is not None and 
            avg_hashrate(lines, 50) < EXPECTED_HASHRATE):
            reboot("Avg hashrate [%.2f MH/s] below threshold [%.2f MH/s], rebooting!" 
                   % (avg_hashrate(lines, 50)/(1024**2), EXPECTED_HASHRATE/(1024**2)))
        
        if disconnected(lines):
            reboot("Disconnected from server, rebooting...")
            
        sleep(15)

if __name__ == "__main__":
    main()
