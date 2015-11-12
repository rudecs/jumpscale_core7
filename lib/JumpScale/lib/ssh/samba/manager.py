import signal
import sys
from StringIO import StringIO
from fabric.api import settings
from JumpScale import j
# from samba.netcmd.main import cmd_sambatool
from sambaparser import SambaConfigParser

CONFIG_FILE = '/etc/samba/smb.conf'
EXCEPT_SHARES = ['global', 'printers', 'homes']
BASEPATH = '/VNASSHARE/'


class SMBUser(object):
    def __init__(self, con, verbose=False):
        # self._smb = cmd_sambatool(self._stdout, self._stderr)
        self.con = con
        self._verbose = verbose

    def _smbrun(self, args):
        output = self.con.run('samba-tool user %s ' % args, warn_only=True)
        lines = output.splitlines()

        return lines

    def _format(self, output):
        if output[0].startswith("Warning:"):
            if self._verbose:
                print output[0]

            return False

        return True

    def list(self):
        output = self._smbrun("list")
        return output

    def remove(self, username):
        output = self._smbrun("delete " + username)
        with self.con.fabric.api.settings(warn_only=True):
            self.con.user_remove(username)
        return self._format(output)

    def add(self, username, password):
        output = self._smbrun("add " + username + " " + password)
        with self.con.fabric.api.settings(warn_only=True):
            self.con.run("bash /etc/samba/update-uid.sh", True, False)
            self.con.user_create(username)
        return self._format(output)

    def grantaccess(self, username, sharename, sharepath, readonly=True):
        sharepath = j.system.fs.joinPaths(BASEPATH, sharepath, sharename)
        if not self.con.dir_exists(sharepath):
            return False
        group = '%s%s' % (sharename, 'r' if readonly else 'rw')
        with self.con.fabric.api.settings(warn_only=True):
            self.con.group_user_add(group, username)
        return True

    def revokeaccess(self, username, sharename, sharepath, readonly=True):
        sharepath = j.system.fs.joinPaths(BASEPATH, sharepath, sharename)
        with self.con.fabric.api.settings(warn_only=True):
            if self.con.dir_exists(sharepath):
                group = '%s%s' % (sharename, 'r' if readonly else 'rw')
                self.con.group_user_del(username, group)
        return True


class SMBShare(object):
    def __init__(self, con):
        self.con = con
        self._config = SambaConfigParser()
        self._load()

    def _load(self):
        if not self.con.file_exists(CONFIG_FILE):
            self.con.dir_ensure(j.system.fs.getParent(CONFIG_FILE))
            self.con.file_ensure(CONFIG_FILE)
        cfg = self.con.file_read(CONFIG_FILE)
        data = StringIO('\n'.join(line.strip() for line in cfg.splitlines()))
        self._config.readfp(data)

    def get(self, sharename):
        # special share which we don't handle
        if sharename in EXCEPT_SHARES:
            return False

        # share name not found
        if not self._config.has_section(sharename):
            return False

        return self._config.items(sharename)

    def list(self):

        shares = self._config.sections()
        # special share which we don't handle
        for sharename in shares[:]:
            if sharename in EXCEPT_SHARES:
                shares.remove(sharename)

        return shares

    def remove(self, sharename):
        # don't touch special shares (global, ...)
        if sharename in EXCEPT_SHARES:
            return False

        if not self._config.has_section(sharename):
            return False

        self._config.remove_section(sharename)
        return True

    def add(self, sharename, path, options={}):
        # share already exists or is denied
        if self._config.has_section(sharename):
            return False

        if sharename in EXCEPT_SHARES:
            return False

        # set default options
        self._config.add_section(sharename)
        self._config.set(sharename, 'path', path)

        # set user defined options
        for option in options:
            self._config.set(sharename, option, options[option])

        return True

    def commit(self):
        sio = StringIO()
        self._config.write(sio)
        self.con.file_write(CONFIG_FILE, sio.getvalue())

        # reload config
        j.system.process.killProcessByName('smbd', signal.SIGHUP)
        j.system.process.killProcessByName('nmbd', signal.SIGHUP)

        return True

    def list(self):
        shares = self._config.sections()
        result = dict()
        for sharename in shares:
            if sharename in EXCEPT_SHARES:
                # special share which we don't handle
                continue
            shareinfo = self._config.items(sharename)
            result[sharename] = {info[0]: info[1] for info in shareinfo}

        return result


class SMBSubShare(object):
    def __init__(self, con):
        self.con = con
        self.con.dir_ensure(BASEPATH)

    def get(self, sharename, sharepath):
        sharepath = j.system.fs.joinPaths(BASEPATH, sharepath, sharename)
        if not self.con.dir_exists(sharepath):
            return False

        acls = dict()
        for access in ['r', 'rw']:
            groupname = '%s%s' % (sharename, access)
            users = self.con.group_check(groupname).get('members', [])
            acls[access] = users

        return {sharename: acls}

    def remove(self, sharename, sharepath):
        sharepath = j.system.fs.joinPaths(BASEPATH, sharepath, sharename)
        self.con.dir_remove(sharepath)
        with self.con.fabric.api.settings(warn_only=True):
            for access in ['r', 'rw']:
                self.con.group_remove('%s%s' % (sharename, access))

        return True

    def add(self, sharename, sharepath):
        # Create dir under BASEPATH
        # Create two groups for access: one readonly and one rw
        sharepath = j.system.fs.joinPaths(BASEPATH, sharepath, sharename)
        self.con.dir_ensure(sharepath, recursive=True)

        with self.con.fabric.api.settings(warn_only=True):
            for access in ['r', 'rw']:
                groupname = '%s%s' % (sharename, access)
                self.con.group_create(groupname)
                self.con.run('setfacl -m g:%s:%s %s' % (groupname, access, sharepath))

        return True

    def list(self, path=''):
        sharepath = j.system.fs.joinPaths(BASEPATH, path)
        subshares = self.con.run('find %s -maxdepth 1 -type d -exec basename {} \;' % sharepath).splitlines()
        result = list()
        for subshare in subshares:
            if subshare == j.system.fs.getBaseName(path):
                continue
            result.append(self.get(subshare, sharepath))
        return result


class Samba:
    def __init__(self, con):
        if not con:
            # make sure key is generated and in authorized keys
            con = j.ssh.connect(keypath='/root/.ssh/id_rsa')
        self._users = SMBUser(con, True)
        self._shares = SMBShare(con)
        self._subshares = SMBSubShare(con)

    def getShare(self, sharename):
        return self._shares.get(sharename)

    def listShares(self):
        return self._shares.list()

    def removeShare(self, sharename):
        return self._shares.remove(sharename)

    def addShare(self, sharename, path, options={}):
        return self._shares.add(sharename, path, options)

    def commitShare(self):
        return self._shares.commit()

    def getSubShare(self, sharename, sharepath):
        return self._subshares.get(sharename)

    def removeSubShare(self, sharename, sharepath):
        return self._subshares.remove(sharename, sharepath)

    def addSubShare(self, sharename, sharepath):
        return self._subshares.add(sharename, sharepath)

    def listSubShares(self, path):
        return self._subshares.list(path)

    def listUsers(self):
        return self._users.list()

    def removeUser(self, username):
        return self._users.remove(username)

    def addUser(self, username, password):
        return self._users.add(username, password)

    def grantaccess(self, username, sharename, sharepath, readonly=True):
        return self._users.grantaccess(username, sharename, sharepath, readonly)

    def revokeaccess(self, username, sharename, sharepath, readonly=True):
        return self._users.revokeaccess(username, sharename, sharepath, readonly)


class SambaFactory(object):

    def _getFactoryEnabledClasses(self):
        return (("", "Samba", Samba()), ("Samba", "SMBUser", SMBUser()), ("Samba", "SMBShare", SMBShare()),
                ("Samba", "SMBSubShare", SMBSubShare()), ("Samba", "SambaConfigParser", SambaConfigParser()))

    def get(self, con):
        return Samba(con)
