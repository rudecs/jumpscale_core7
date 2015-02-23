from JumpScale import j

def cb():
    from .GitFactory import GitFactory
    return GitFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('git', cb)

