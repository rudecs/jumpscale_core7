from JumpScale import j

def cb():
    from .MySQLFactory import MySQLFactory
    return MySQLFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('mysql', cb)
