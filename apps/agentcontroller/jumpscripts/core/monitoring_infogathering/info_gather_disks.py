from JumpScale import j

descr = """
Checks disks' status
"""

organization = "jumpscale"
name = 'check_disks'
author = "zains@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"

async = True
queue = 'process'
roles = []
enable = True
period = 600

log = True


def action():
    import JumpScale.lib.diskmanager
    result = dict()
    pattern = None

    if j.application.config.exists('gridmonitoring.disk.pattern'):
        pattern = j.application.config.getStr('gridmonitoring.disk.pattern')

    disks = j.system.platform.diskmanager.partitionsFind(
        mounted=True, prefix='', minsize=0, maxsize=None)
    for disk in disks:
        if pattern and j.codetools.regex.match(pattern, disk.path) == True:
            # pattern is a blacklist, continue if match
            continue
        result[disk.path] = {'free': disk.free, 'size': disk.size, 'mountpoint': disk.mountpoint}

    results = list()

    for path, disk in list(result.items()):
        result = {'category': 'Disks'}
        result['path'] = path
        checkusage = not (disk['mountpoint'] and j.system.fs.exists(j.system.fs.joinPaths(disk['mountpoint'], '.dontreportusage')))

        if checkusage and ((disk['free'] and disk['size']) and (disk['free'] / float(disk['size'])) * 100 < 10):
            result['message'] = 'FREE SPACE LESS THAN 10%% on disk %s %s' % (path, disk['mountpoint'])
            result['state'] = 'ERROR'
        else:
            if disk['free']:
                size, unit = j.tools.units.bytes.converToBestUnit(disk['free'], 'M')
                result['message'] = '%.2f %siB free space available on %s' % (size, unit, path)

            else:
                result['message'] = 'Disk %(path)s is not mounted, Info is not available' % result
            result['state'] = 'OK'
        results.append(result)

    if not results:
        results.append({'message': 'No disks available', 'state': 'OK', 'category': 'Disks'})

    return results

if __name__ == "__main__":
    print action()
