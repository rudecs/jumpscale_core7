from JumpScale import j

descr = """
Checks disks' status
"""

organization = "jumpscale"
name = 'check_disks'
author = "zains@codescalers.com"
license = "bsd"
version = "1.0"
category = "system.disks"

async = True
queue = 'process'
roles = []
enable = True
period=0

log=False

def action():
    import JumpScale.lib.diskmanager
    result = dict()
    disks = j.system.platform.diskmanager.partitionsFind(mounted=True, prefix='', minsize=0, maxsize=None)
    for disk in disks:
        result[disk.path] = {'free': disk.free, 'size': disk.size}
    return result

if __name__ == "__main__":
    print action()