from JumpScale import j

def cb():
    from .nginx import NginxFactory
    return NginxFactory()

j.base.loader.makeAvailable(j, 'system.platform')
j.system.platform._register('nginx', cb)
