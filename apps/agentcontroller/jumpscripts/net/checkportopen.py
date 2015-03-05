
from JumpScale import j
from JumpScale.baselib import gitlab
from JumpScale.baselib import git
import subprocess
import sys

descr = """
Clone/Update gitlab user spaces
"""

organization = "jumpscale"
name = "checkportopen"
author = "hamdy.farag@codescalers.com"
license = "bsd"
version = "1.0"
async=True
roles = []
log=False


def action(port):
    print "Checking TCP/UDP port (%s) open " % str(port)
    print "**********************************************"
    res = subprocess.call(["netstat  -ano   | grep %s" % str(port)], shell=True)
    if res == 0:
        return True
    return False

if __name__ == '__main__':
    if not len(sys.argv) == 2:
        print "Usage: python checkportopen.py port"
    else:
        action(sys.argv[1])
