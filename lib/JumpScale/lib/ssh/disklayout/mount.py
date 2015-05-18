from JumpScale import j
from fabric.api import settings


class MountError(Exception):
    pass


class Mount(object):
    def __init__(self, con, device, path=None, options=''):
        self._con = con
        self._device = device
        self._path = path
        self._autoClean = False
        if self._path is None:
            self._path = j.system.fs.getTmpDirPath()
            self._autoClean = True
        self._options = options

    @property
    def _mount(self):
        return 'mount {options} {device} {path}'.format(
            options='-o ' + self._options if self._options else '',
            device=self._device,
            path=self._path
        )

    @property
    def _umount(self):
        return 'umount {path}'.format(path=self._path)

    @property
    def path(self):
        return self._path

    def __enter__(self):
        return self.mount()

    def __exit__(self, type, value, traceback):
        return self.umount()

    def mount(self):
        with settings(abort_exception=MountError):
            self._con.dir_ensure(self.path, recursive=True)
            self._con.run(self._mount)

        return self

    def umount(self):
        with settings(abort_exception=MountError):
            self._con.run(self._umount)
            if self._autoClean:
                self._con.dir_remove(self.path)
        return self
