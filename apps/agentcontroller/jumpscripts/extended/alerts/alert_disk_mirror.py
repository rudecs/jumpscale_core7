
from JumpScale import j

descr = """
Check on disk mirroring
"""

organization = "jumpscale"
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
period = 60  # always in sec
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
    except Exception:
        return
    import re
    keys = j.application.config.getKeysFromPrefix('storage')
    if not keys:
        return

    devices = dict()
    for key in keys:
        keyid = key.split('.')[1]
        devices.setdefault(keyid, dict())
        keytype = 'type' if 'type' in key else 'devices'
        devices[keyid][keytype] = j.application.config.get(key) 

    for key, device in devices.iteritems():
        fstype = device['type']
        devs = device['devices'].split(',')

        if fstype == 'btrfs':
            btrfsdata = j.system.process.execute('btrfs filesystem show').replace('\n', '')
            lines = btrfsdata.split('Label:')
            for line in lines:
                if devs[0] in line:
                    for dev in devs[1:]:
                        if dev not in line:
                            j.tools.watchdog.client.send("disk.mirror", 'CRITICAL', -1)
                            break

        elif fstype.startswith('raid'):
            mdstat = j.system.fs.fileGetContents('/proc/mdstat')
            if fstype not in mdstat:
                j.tools.watchdog.client.send("disk.mirror", 'CRITICAL', -1)
            else:
                line = re.findall('.*%s.*' % devs[0], mdstat)[0]
                for dev in devs[1:]:
                    if dev not in line:
                        j.tools.watchdog.client.send("disk.mirror", 'CRITICAL', -1)
                        break
