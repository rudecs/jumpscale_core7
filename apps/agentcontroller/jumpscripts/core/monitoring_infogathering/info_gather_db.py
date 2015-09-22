from JumpScale import j

descr = """
Checks databases' status
"""

organization = "jumpscale"
name = 'info_gather_db'
author = "zains@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"

async = False
roles = []
enable = True
period=0

log=False

def action():
    import JumpScale.grid.osis
    osiscl = j.clients.osis.getByInstance('main')
    status = osiscl.getStatus()
    return {'results': status, 'errors':[]}

if __name__ == "__main__":
    print action()