from JumpScale import j
import JumpScale.grid.osis

descr = """
heartbeat in process to osis
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "system.heartbeat"
startatboot = True
period = 60 #always in sec
timeout = period * 0.2
order = 1
enable = True
async = False
roles=["*"]

def action():
    osiscl = j.clients.osis.getByInstance()
    hbcl = j.core.osis.getCategory(osiscl, 'system', 'heartbeat')
    obj = hbcl.new()
    hbcl.set(obj)

