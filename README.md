This script tracks the "error log" from qtminer and looks for patterns
that suggests that the mining has stopped. If found, the computer is rebooted.
In order for this to work, the stderr of qtminer has to be set to ~/nanny/error.

> qtminer -<your usual options> 2> ~/nanny/error

Make sure that /sbin/reboot doesn't require sudo:

> sudo chmod u+s /sbin/reboot

Don't forget set this script to start-on-boot
