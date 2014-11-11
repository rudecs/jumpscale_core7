from JumpScale import j

descr = """
This jumpscript returns network info
"""

#optional info
organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"

@queue("io")
def getNetworkInfo():
    return j.system.net.getNetworkInfo()
