from JumpScale import j
from . import lsblk
from . import mount


class DiskManagerFactory(object):
    def get(self, connection):
        """
        Return disk manager for that cuisine connection.
        """
        return DiskManager(connection)


class DiskManager(object):
    def __init__(self, con):
        self.con = con

    def _loadhrd(self, mount):
        hrdpath = j.system.fs.joinPaths(mount, '.disk.hrd')
        if self.con.file_exists(hrdpath):
            return j.core.hrd.get(content=self.con.file_read(hrdpath))

    def getinfo(self):
        output = self.con.run(lsblk.COMMAND)
        disks = lsblk.parse(self.con, output)

        # loading hrds
        for disk in disks:
            for partition in disk.partitions:
                if partition.fstype == 'swap':
                    continue

                if partition.mount and partition.fstype != 'btrfs':
                    # partition is already mounted, no need to remount it
                    hrd = self._loadhrd(partition.mount)
                elif partition.fstype:
                    with mount.Mount(self.con, partition.name,
                                     options='ro') as mnt:
                        hrd = self._loadhrd(mnt.path)

                partition.hrd = hrd
        return disks
