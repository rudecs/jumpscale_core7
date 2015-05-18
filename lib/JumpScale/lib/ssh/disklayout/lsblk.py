import re


COMMAND = 'lsblk -bnP -o NAME,TYPE,UUID,FSTYPE,SIZE,MOUNTPOINT -e 7,1'

_extract_pattern = re.compile('\s*([^=]+)="([^"]*)"')


class BlkInfo(object):
    def __init__(self, name, type, size):
        self.name = name
        self.type = type
        self.size = size

    def __str__(self):
        return '%s %s' % (self.name, self.size)

    def __repr__(self):
        return str(self)


class DiskInfo(BlkInfo):
    def __init__(self, name, size):
        super(DiskInfo, self).__init__(name, 'disk', size)
        self.partitions = list()


class PartitionInfo(BlkInfo):
    def __init__(self, name, size, uuid, fstype, mount):
        super(PartitionInfo, self).__init__(name, 'part', size)
        self.uuid = uuid
        self.fstype = fstype
        self.mount = mount
        self.hrd = None


def parse(output):
    """
    Parses the output of command
    `lsblk -abnP -o NAME,TYPE,UUID,FSTYPE,SIZE`

    Output must look like that
    NAME="sda" TYPE="disk" UUID="" FSTYPE="" SIZE="256060514304"
    NAME="sda1" TYPE="part" UUID="1db378f5-4e49-4fb7-8000-051fe77b23ea"
        FSTYPE="btrfs" SIZE="256059465728"
    NAME="sr0" TYPE="rom" UUID="" FSTYPE="" SIZE="1073741312"
    """
    disks = []
    disk = None
    for line in output.split('\n'):
        info = dict(_extract_pattern.findall(line))
        name = '/dev/%s' % info['NAME']
        if info['TYPE'] == 'disk':
            disk = DiskInfo(name, info['SIZE'])
            disks.append(disk)
        elif info['TYPE'] == 'part':
            if disk is None:
                raise Exception(
                    ('Parition "%s" does not have a parent disk' %
                        info['NAME'])
                )
            part = PartitionInfo(name, info['SIZE'],
                                 info['UUID'], info['FSTYPE'],
                                 info['MOUNTPOINT'])
            disk.partitions.append(part)
        else:
            # don't care about outher types.
            disk = None

    return disks
