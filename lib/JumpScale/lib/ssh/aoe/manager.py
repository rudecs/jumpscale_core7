import re
from JumpScale import j

from fabric.api import settings


CMD_LS_PATTERN = re.compile(
    '^\s*(\d+)\s+(.+?)\s*$',
    re.MULTILINE
)
# 30605 /usr/sbin/vblade 0 1 eth0 /storage/storage1.img
CMD_PS_PATTERN = re.compile(
    '^\s*(\d+)\s+.*?vblade\s+(\d+)\s+(\d+)\s+([^\s]+)\s+(.+?)\s*$',
    re.MULTILINE
)


class AOEError(Exception):
    pass


class AOEFactory(object):
    def get(self, con):
        return AOEManager(con)


class VDisk(object):
    def __init__(self, pid, major, minor, inf, path, size):
        self._pid = pid
        self._major = major
        self._minor = minor
        self._inf = inf
        self._path = path
        self._size = int(size)

    @property
    def pid(self):
        return self._pid

    @property
    def path(self):
        return self._path

    @property
    def major(self):
        return self._major

    @property
    def minor(self):
        return self._minor

    @property
    def inf(self):
        return self._inf

    @property
    def size(self):
        return self._size

    @property
    def exposed(self):
        return self._pid is not None

    def __str__(self):
        if self.exposed:
            return 'exposed {path}:{size} {major}:{minor} {inf}'.format(
                path=self.path,
                size=self.size,
                major=self.major,
                minor=self.minor,
                inf=self.inf
            )
        else:
            return 'unexposed {path}:{size}'.format(
                path=self.path, size=self.size
            )

    def __repr__(self):
        return str(self)


class AOEManager(object):
    def __init__(self, con):
        self._con = con

    def list(self, storpath="/mnt/disktargets/"):
        """
        List all vdisks under this location.
        Note that all files in that directory are assumed to be valid images
        """
        disks = []
        with settings(abort_exception=AOEError):
            # list all files in directory
            ls = self._con.run(
                'find {path} -maxdepth 1 -type f -printf "%s %f\n"'.format(
                    path=storpath
                )
            )
            files = {}
            for match in CMD_LS_PATTERN.finditer(ls):
                size, name = match.groups()
                files[j.system.fs.joinPaths(storpath, name)] = size

            ps = self._con.run('ps -o pid,cmd -C vblade; true')

            for match in CMD_PS_PATTERN.finditer(ps):
                pid, major, minor, inf, path = match.groups()
                vdisk = VDisk(pid, major, minor, inf, path, files.get(path, 0))
                if vdisk.path in files:
                    disks.append(vdisk)
                    del files[vdisk.path]
            for path, size in files.iteritems():
                disks.append(VDisk(None, None, None, None, path, size))

        return disks

    def create(self, storpath, size=10):
        """
        Create and vdisk

        :storpath: is the full image path.
        :size: size in GB
        """
        base = j.system.fs.getDirName(storpath)

        with settings(abort_exception=AOEError):
            self._con.dir_ensure(base, True, mode=755)
            cmd = 'dd if=/dev/zero of={path} bs=1G count=0 seek={size}'.format(
                path=storpath,
                size=size
            )

            self._con.run(cmd)

        for vdisk in self.list(base):
            if vdisk.path == storpath:
                return vdisk
        raise Exception("Unexpected error, disk not found")

    def expose(self, storage, major, minor, inf):
        """
        Expose the given image on major:minor and interface

        :storage: the image path or vdisk
        :major: Major number (shelf)
        :minor: Minor number (slot)
        :inf: Network interface
        """
        path = None
        if isinstance(storage, VDisk):
            path = storage.path
        elif isinstance(storage, basestring):
            path = storage

        if not path:
            raise ValueError('Invalid path')

        with settings(abort_exception=AOEError):
            self._con.run(
                'nohup vbladed {major} {minor} {inf} {path}'.format(
                    major=major,
                    minor=minor,
                    inf=inf,
                    path=path
                )
            )

    def unexpose(self, storage):
        """
        Unexpose the storage
        """

        vdisk = None
        if isinstance(storage, VDisk):
            vdisk = storage
        elif isinstance(storage, basestring):
            base = j.system.fs.getDirName(storage)
            for disk in self.list(base):
                if disk.path == storage:
                    vdisk = disk
                    break

        if vdisk is None:
            raise ValueError('Invalid disk')

        if not vdisk.exposed:
            return

        with settings(abort_exception=AOEError):
            self._con.run('kill %s' % vdisk.pid)

    def delete(self, path):
        self.unexpose(path)

        with settings(abort_exception=AOEError):
            self._con.run('rm -f %s' % path)
