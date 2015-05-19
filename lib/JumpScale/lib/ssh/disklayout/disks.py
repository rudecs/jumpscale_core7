import re

from fabric.api import settings

from JumpScale import j
from . import mount


class FormatError(Exception):
    pass


class PartitionError(Exception):
    pass


_formatters = {
    # specific format command per filesystem.
    'ntfs': lambda name, fstype: 'mkfs.ntfs -f {name}'.format(name=name)
}


def _default_formatter(name, fstype):
    return 'mkfs.{fstype} {name}'.format(
        fstype=fstype,
        name=name
    )


class BlkInfo(object):
    def __init__(self, con, name, type, size):
        self.con = con
        self.name = name
        self.type = type
        self.size = size

    def __str__(self):
        return '%s %s' % (self.name, self.size)

    def __repr__(self):
        return str(self)


class DiskInfo(BlkInfo):
    def __init__(self, con, name, size):
        super(DiskInfo, self).__init__(con, name, 'disk', size)
        self.partitions = list()

    def _getpart(self):
        ptable = self.con.run(
            'parted -sm {name} unit B print'.format(name=self.name)
        )
        read_disk_next = False
        disk = {}
        partitions = []
        for line in ptable.split('\n'):
            line = line.strip()
            if line == 'BYT;':
                read_disk_next = True
                continue

            parts = line.split(':')
            if read_disk_next:
                # /dev/sdb:8589934592B:scsi:512:512:gpt:ATA VBOX HARDDISK;
                size = int(parts[1][:-1])
                table = parts[5]

                disk.update(
                    size=size,
                    table=table,
                )
                read_disk_next = False
                continue

            # 1:1048576B:2097151B:1048576B:btrfs:primary:;
            partition = {
                'number': int(parts[0]),
                'start': int(parts[1][:-1]),
                'end': int(parts[2][:-1]),
            }

            partitions.append(partition)

        disk['partitions'] = partitions
        return disk

    def _findFreeSpot(self, parts, size):
        if size > parts['size']:
            return
        start = 20 * 1024  # start from 20k offset.
        for partition in parts['partitions']:
            if partition['start'] - start > size:
                return start, start + size
            start = partition['end'] + 1

        if start + size > parts['size']:
            return

        return start, start + size

    def format(self, size, hrd):
        """
        Create new partition and format it as configured in hrd file

        :size: in bytes
        :hrd: the disk hrd info
        """
        # TODO: Validate HRD file

        parts = self._getpart()
        spot = self._findFreeSpot(parts, size)
        if not spot:
            raise Exception('No enough space on disk to allocate')

        start, end = spot
        with settings(abort_exception=FormatError):
            self.con.run(
                ('parted -s /dev/sdb unit B ' +
                    'mkpart primary {start} {end}').format(start=start,
                                                           end=end)
            )

        numbers = map(lambda p: p['number'], parts['partitions'])
        newparts = self._getpart()
        newnumbers = map(lambda p: p['number'], newparts['partitions'])
        number = list(set(newnumbers).difference(numbers))[0]

        partition = PartitionInfo(
            self.con,
            name='%s%d' % (self.name, number),
            size=size,
            uuid='',
            fstype=hrd.get('filesystem'),
            mount=hrd.get('mountpath', '')
        )

        partition.hrd = hrd

        partition.format()
        self.partitions.append(partition)
        return partition


class PartitionInfo(BlkInfo):
    def __init__(self, con, name, size, uuid, fstype, mount):
        super(PartitionInfo, self).__init__(con, name, 'part', size)
        self.uuid = uuid
        self.fstype = fstype
        self.mount = mount
        self.hrd = None

    def _formatter(self, name, fstype):
        fmtr = _formatters.get(fstype, _default_formatter)
        return fmtr(name, fstype)

    def format(self):
        """
        Reformat the partition according to hrd
        """
        if self.mount:
            raise Exception('Partition is mounted on %s' % self.mount)

        if self.hrd is None:
            raise Exception('No HRD attached to disk')

        fstype = self.hrd.get('filesystem')
        command = self._formatter(self.name, fstype)
        with settings(abort_exception=FormatError):
            self.con.run(command)
            with mount.Mount(self.con, self.name) as mnt:
                filepath = j.system.fs.joinPaths(
                    mnt.path,
                    '.disk.hrd'
                )
                self.con.file_write(filepath, content=str(self.hrd),
                                    mode=400)

    def delete(self, force=False):
        """Delete partition"""
        if self.mount:
            raise PartitionError('Partition is mounted on %s' % self.mount)

        if self.hrd is None:
            raise PartitionError('No HRD attached to disk')

        if self.hrd.get('protected', 1) and not force:
            raise PartitionError('Partition is protected')

        m = re.match('^(.+)(\d+)$', self.name)
        number = int(m.group(2))
        device = m.group(1)

        command = 'parted -s {device} rm {number}'.format(
            device=device,
            number=number
        )
        with settings(abort_exception=PartitionError):
            self.con.run(command)

    def mount(self):
        """Mount partition"""

        if self.hrd is None:
            raise Exception('No HRD attached to disk')

        mnt = mount.Mount(self.name, self.hrd.get('mountpath'))
        mnt.mount()
        return mnt
