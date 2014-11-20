# this must be in the beginning so things are patched before ever imported by other libraries
#from gevent import monkey
# monkey.patch_all()
#monkey.patch_socket()
#monkey.patch_ssl()
#monkey.patch_thread()
#monkey.patch_time()

import time
from JumpScale import j
import JumpScale.portal

import sys

if __name__ == '__main__':

    # args=sys.argv
    # instance=args[1]

    # jp = j.packages.findNewest('jumpscale', 'portal')
    # jp = jp.load(instance=instance)
    hrdstring = """
changed:True
osis_connection:main
portal_ipaddr:localhost
portal_name:main
portal_port:82
    """
    j.application.instanceconfig = j.core.hrd.getHRD('/opt/jumpscale7/hrd/jumpscale')

    j.application.start("portal")

    server=j.core.portal.getServer()
    server.start()


    j.application.stop()
