**Nanny**

This script tracks the "error log" from qtminer and looks for patterns
that suggests that the mining has stopped. If found, the computer is rebooted.
In order for this to work, the stderr of qtminer has to be set to ~/nanny/error.

<code>$ qtminer -\<your usual options\> 2> ~/nanny/error </code>

Make sure that /sbin/reboot doesn't require sudo:

<code>$ sudo chmod u+s /sbin/reboot </code>

Don't forget set this script to start-on-boot
