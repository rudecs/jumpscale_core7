
from JumpScale import j


def ubuntu():
    from .ubuntu import manager
    return manager.UbuntuManagerFactory()

def unix():
    from .unix import manager
    return manager.UnixManagerFactory()


def disklayout():
    from .disklayout import manager
    return manager.DiskManagerFactory()


def openwrt():
    from .openwrt import manager
    return manager.OpenWRTFactory()


def nginx():
    from .nginx import manager
    return manager.NginxManagerFactory()


def ufw():
    from .ufw import manager
    return manager.UFWManagerFactory()


def server():
    from .server import manager
    return manager.SSHFactory()


def nfs():
    from .nfs import manager
    return manager.NFSFactory()


def aoe():
    from .aoe import manager
    return manager.AOEFactory()


def rsync():
    from .rsync import manager
    return manager.RsyncFactory()

def samba():
    from .samba import manager
    return manager.SambaFactory()



def connect(addr='localhost', port=22, passwd=None,verbose=True,keypath=None):

    if keypath=="":
        keypath=None

    c=j.remote.cuisine.connect(addr, port=22, passwd=passwd)
    if keypath!=None:
        c.fabric.key_filename=keypath
        c.fabric.api.env["key_filename"]=keypath
        if not j.do.exists(keypath):
            j.events.opserror_critical("cannot find key:%s"%keypath)
    c.fabric.api.env['connection_attempts'] = 5

    if not verbose:
        c.fabric.state.output["running"]=False
        c.fabric.state.output["stdout"]=False
    j.ssh.connection = c
    return c

j.base.loader.makeAvailable(j, 'ssh')

j.ssh.connect = connect

j.ssh._register('disklayout', disklayout)
j.ssh._register('openwrt', openwrt)
j.ssh._register('nginx', nginx)
j.ssh._register('ufw', ufw)
j.ssh._register('ubuntu', ubuntu)
j.ssh._register('server', server)
j.ssh._register('nfs', nfs)
j.ssh._register('aoe', aoe)
j.ssh._register('unix', unix)
j.ssh._register('rsync', rsync)
j.ssh._register('samba', samba)
