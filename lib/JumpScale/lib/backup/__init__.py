from JumpScale import j

from .BackupFactory import *
import JumpScale.baselib.hash

j.base.loader.makeAvailable(j, 'clients')

j.clients.backup=BackupFactory()
