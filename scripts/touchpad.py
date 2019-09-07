#!/usr/bin/python3
"""The laptop MSI p63 modern does not support sleep mode in linux,
so i made this script to remove the touchpad module before putting
the sleep mode on, then reload the module at resume.

the script relies on systemd
copy this file into: /usr/lib/systemd/system-sleep
"""

from subprocess import run
import sys


MODULE = 'i2c_hid'

if __name__ == "__main__":
    argc = len(sys.argv)
    if argc < 2:
        raise ValueError
    if sys.argv[1] == 'pre':
        run(['rmmod', MODULE], check=True)
    elif sys.argv[1] == 'post':
        run(['modprobe', MODULE], check=True)
