from JumpScale import j
from fabric.api import settings


OP_ADD = '+'
OP_DEL = '-'
OP_ERS = '--'


class SSHError(Exception):
    pass

class SSH(object):
    SSH_ROOT = '~/.ssh'
    SSH_AUTHORIZED_KEYS = j.system.fs.joinPaths(SSH_ROOT, 'authorized_keys')

    def __init__(self, con=None):
        self._con = con
        self._keys = None
        self._transactions = []

    @property
    def keys(self):
        if self._keys is None:
            with settings(abort_exception=SSHError):
                self._con.dir_ensure(SSH.SSH_ROOT)
                if self._con.file_exists(SSH.SSH_AUTHORIZED_KEYS):
                    self._keys = filter(None, self._con.file_read(
                        SSH.SSH_AUTHORIZED_KEYS
                    ).split('\n'))
                else:
                    self._keys = []

        return self._keys

    def addKey(self, key):
        """
        Add pubkey to authorized_keys
        """
        self._transactions.append(
            (OP_ADD, key.strip())
        )

    def deleteKey(self, key):
        """
        Delete pubkey from authorized_keys
        """
        self._transactions.append(
            (OP_DEL, key.strip())
        )

    def erase(self):
        """
        Erase all keys from authorized_keys
        """
        self._transactions.append(
            (OP_ERS, None)
        )

    def commit(self):
        """
        Apply all pending changes to authorized_keys
        """
        keys = set(self.keys)
        with settings(abort_exception=SSHError):
            while self._transactions:
                op, key = self._transactions.pop(0)
                if op == OP_ERS:
                    keys = set()
                elif op == OP_ADD:
                    keys.add(key)
                elif op == OP_DEL:
                    keys.discard(key)

            self._con.file_write(SSH.SSH_AUTHORIZED_KEYS, '\n'.join(keys))

        # force reload on next access.
        self._keys = None

    def disableNonKeyAccess(self):
        """
        Disable passowrd login to server. This action doens't require
        calling to commit and applies immediately. So if you added your key
        make sure to commit it before you call this method.
        """

        with settings(abort_exception=SSHError):
            self._con.file_append(
                '/etc/ssh/sshd_config',
                'PasswordAuthentication no'
            )

            self._con.upstart_reload('ssh')

class SSHFactory(object):
    def _getFactoryEnabledClasses(self):
        return ([("","SSH",SSH())])

    def get(self, con=None):
        if con==None:
            con=j.ssh.connection
        return SSH(con)
