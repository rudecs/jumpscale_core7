from JumpScale import j

def cb():
    from rogerthat import RogerthatFactory
    return RogerthatFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('rogerthat', cb)
