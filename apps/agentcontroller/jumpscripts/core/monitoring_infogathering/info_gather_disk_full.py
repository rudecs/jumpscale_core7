
from JumpScale import j

descr = """
Check on disk fullness
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
period = 5 * 60  # always in sec
timeout = period * 0.2
startatboot = True
order = 1
enable = True
async = True
log = True
queue ='process'
roles = []


def action():
    import psutil
    mounteddisks = psutil.disk_partitions()
    results = list()
    for disk in mounteddisks:
        result = dict()
        if disk.mountpoint:
            usage = psutil.disk_usage(disk.mountpoint)
            message = "Disk %s mounted at %s on node %s:%s reached %s%%" % (disk.device, disk.mountpoint, j.application.whoAmI.gid, j.application.whoAmI.nid, usage.percent)
            result['message'] = message
            result['category'] = 'Disks'
            result['state'] = 'OK'
            if usage.percent > 95:
                j.errorconditionhandler.raiseOperationalCritical(message, 'monitoring', die=False)
                result['state'] = 'ERROR'
            elif usage.percent > 90:
                j.errorconditionhandler.raiseOperationalWarning(message, 'monitoring')
                result['state'] = 'WARNING'
            
        results.append(result)
    return results
    
if __name__ == '__main__':
    print action()
