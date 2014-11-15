from JumpScale import j
from .HgLibFactory import HgLibFactory
j.base.loader.makeAvailable(j, 'clients')
j.clients.mercurial = HgLibFactory()

try:
    import mercurial
except ImportError:
    j.system.platform.ubuntu.checkInstall("mercurial","hg")
