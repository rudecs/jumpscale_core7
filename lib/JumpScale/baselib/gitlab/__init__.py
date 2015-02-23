from JumpScale import j

def cb():
    from .GitlabFactory import GitlabFactory
    return GitlabFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('gitlab', cb)
