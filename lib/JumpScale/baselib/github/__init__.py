from JumpScale import j

def cb():
    from .github import GitHubFactory
    return GitHubFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('github', cb)
