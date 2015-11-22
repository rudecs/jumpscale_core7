from JumpScale import j

descr = """
Checks databases' status
"""

organization = "jumpscale"
name = 'info_gather_db'
author = "zains@codescalers.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
category = "system.dbstatus"

async = False
roles = []
enable = True
period=0

log=True

def action():
    import JumpScale.grid.osis
    osiscl = j.clients.osis.getByInstance('main')
    status = osiscl.getStatus()
    if status['mongodb'] == False :
        j.errorconditionhandler.raiseOperationalCritical('mongodb status -> halted', 'monitoring', die=False)
    if status['influxdb'] == False :
        j.errorconditionhandler.raiseOperationalCritical('influxdb status -> halted', 'monitoring', die=False)
    return status

if __name__ == "__main__":
    print action()
