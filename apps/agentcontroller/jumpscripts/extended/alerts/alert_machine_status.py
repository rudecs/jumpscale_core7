
from JumpScale import j

descr = """
Check on machine status
"""

organization = "jumpscale"
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
period = 60*5  # always in sec
startatboot = True
order = 1
enable = False
async = True
log = False
queue ='process'
roles = []


def action():
    try:
        import JumpScale.baselib.watchdog.client
        import libvirt
    except Exception:
        return

    import JumpScale.grid.osis
    ocl = j.clients.osis.getByInstance('main')
    mcl = j.clients.osis.getCategory(ocl, 'cloudbroker', 'vmachine')

    try:
        con = libvirt.open('qemu:///system')
        stateMap = {libvirt.VIR_DOMAIN_RUNNING: 'RUNNING',
                    libvirt.VIR_DOMAIN_NOSTATE: 'NOSTATE',
                    libvirt.VIR_DOMAIN_PAUSED: 'PAUSED'}

        domains = con.listAllDomains()
        for domain in domains:
            domainname = domain.name().split('-')[1]
            machine = mcl.get(domainname)
            state = machine['state']
            livestate = stateMap.get(domain.state()[0], 'STOPPED')
            if state == 'RUNNING' and livestate != 'RUNNING':
                message = 'Machine %s is down, but reported running in OSIS' % machine['id']
                j.tools.watchdog.client.send("machine.status","CRITICAL", message)
            if livestate == 'RUNNING' and state != 'RUNNING':
                message = 'Machine %s is running, but reported down in OSIS' % machine['id']
                j.tools.watchdog.client.send("machine.status","WARNING", message)
    finally:
        con.close()
