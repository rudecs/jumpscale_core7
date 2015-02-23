from JumpScale import j

def cb():
    from .PostgresqlFactory import PostgresqlFactory
    return PostgresqlFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('postgres', cb)
