from JumpScale import j

def cb():
    from .QSocketServer import QSocketServer, QSocketServerFactory
    return QSocketServerFactory()

j.base.loader.makeAvailable(j, 'system')
j.system._register('socketserver', cb)
