from JumpScale import j

def cb():
    try:
        import mercurial
    except ImportError:
        j.system.platform.ubuntu.checkInstall("mercurial","hg")
    from .HgLibFactory import HgLibFactory
    return HgLibFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('mercurial', cb)
