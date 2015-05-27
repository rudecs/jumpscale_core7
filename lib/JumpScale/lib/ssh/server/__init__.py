from JumpScale import j
from fabric.api import settings


class SSHError(Exception):
    pass


class SSHFactory(object):
    def get(self, con):
        return SSH(con)


class SSH(object):
    SSH_ROOT = '~/.ssh'
    SSH_AUTHORIZED_KEYS = j.system.fs.joinPaths(SSH_ROOT, 'authorized_keys')

    def __init__(self, con):
        self._con = con

    def addKey(self, key):
        with settings(abort_exception=SSHError):
            self._con.dir_ensure(SSH.SSH_ROOT)
            self._con.file_append(SSH.SSH_AUTHORIZED_KEYS, key)

    def deleteKey(self, key):
        key = key.strip()
        with settings(abort_exception=SSHError):
            self._con.dir_ensure(SSH.SSH_ROOT)
            if not self._con.file_exists(SSH.SSH_AUTHORIZED_KEYS):
                return

            keys_str = self._conf.file_read(SSH.SSH_AUTHORIZED_KEYS)
            found = False
            keys = []
            for line in keys_str.split('\n'):
                if line != key:
                    keys.append(line)
                else:
                    found = True

            if found:
                self._con.file_write(SSH.SSH_AUTHORIZED_KEYS, '\n'.join(keys))

    def erease(self):
        with settings(abort_exception=SSHError):
            self._con.dir_ensure(SSH.SSH_ROOT)
            self._con.file_write(SSH.SSH_AUTHORIZED_KEYS, '')

    def disableNonKeyAccess(self):
        pass
