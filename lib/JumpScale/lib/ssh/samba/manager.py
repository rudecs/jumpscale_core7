import signal
import sys
from StringIO import StringIO
from fabric.api import settings
from JumpScale import j
# from samba.netcmd.main import cmd_sambatool
from sambaparser import SambaConfigParser

CONFIG_FILE = '/etc/samba/smb.conf'
EXCEPT_SHARES = ['global', 'printers', 'homes']

class SambaFactory(object):
    def get(self, con):
        return Samba(con)

class SMBUser(object):
    def __init__(self, verbose=False):
        # self._smb = cmd_sambatool(self._stdout, self._stderr)
        self._verbose = verbose
    
    def _smbrun(self, args):
        output = j.system.process.run("samba-tool user " + args, False, True, 10, False)
        
        # if stdout is empty, we return the first line of stderr
        if output[1] == '':
            lines = output[2].split('\n')
            lines = [lines[0], 0]
        else:
            lines = output[1].split('\n')
        
        lines.pop()
        return lines
    
    def _format(self, output):
        if output[0].startswith("ERROR("):
            if self._verbose:
                print output[0]
            
            return False
        
        return True
    
    def list(self):
        output = self._smbrun("list")
        return output
        
    def remove(self, username):
        output = self._smbrun("delete " + username)
        return self._format(output)
    
    def add(self, username, password):
        output = self._smbrun("add " + username + " " + password)
        j.system.process.run("bash /etc/samba/update-uid.sh", True, False)
        return self._format(output)

class SMBShare(object):
    def __init__(self):
        self._config = SambaConfigParser()
        self._load()

    def _load(self):
        data = StringIO('\n'.join(line.strip() for line in open(CONFIG_FILE)))
        self._config.readfp(data)
    
    def get(self, sharename):
        # special share which we don't handle
        if sharename in EXCEPT_SHARES:
            return False
            
        # share name not found
        if not self._config.has_section(sharename):
            return False
        
        return self._config.items(sharename)
        
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
        with open(CONFIG_FILE, 'wb') as configfile:
            self._config.write(configfile)
        
        # reload config
        j.system.process.killProcessByName('smbd', signal.SIGHUP)
        j.system.process.killProcessByName('nmbd', signal.SIGHUP)
            
        return True

class Samba:
    def __init__(self, con):
        self._users = SMBUser(True)
        self._shares = SMBShare()
        self._con = con;
    
    def getShare(self, sharename):
        return self._shares.get(sharename)
        
    def removeShare(self, sharename):
        return self._shares.remove(sharename)
        
    def addShare(self, sharename, path, options={}):
        return self._shares.add(sharename, path, options)
        
    def commitShare(self):
        return self._shares.commit()
    
    def listUsers(self):
        return self._users.list()
    
    def removeUser(self, username):
        return self._users.remove(username)
    
    def addUser(self, username, password):
        return self._users.add(username, password)
