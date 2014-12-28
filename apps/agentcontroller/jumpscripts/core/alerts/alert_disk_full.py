
from JumpScale import j

descr = """
Check on disk fullness
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
license = "bsd"
version = "1.0"
period = 5 * 60  # always in sec
startatboot = True
order = 1
enable = True
async = True
log = False
queue ='process'
roles = []


def action():
    import psutil
    mounteddisks = psutil.disk_partitions()
    for disk in mounteddisks:
        if disk.mountpoint:
            usage = psutil.disk_usage(disk.mountpoint)
            message = "Disk %s mounted at %s on node %s:%s reached %s%%" % (disk.device, disk.mountpoint, j.application.whoAmI.gid, j.application.whoAmI.nid, usage.percent)
            if usage.percent > 90:
                j.errorconditionhandler.raiseOperationalWarning(message, 'monitoring')
            elif usage.percent > 95:
                j.errorconditionhandler.raiseOperationalCritical(message, 'monitoring', die=False)

if __name__ == '__main__':
    action()
