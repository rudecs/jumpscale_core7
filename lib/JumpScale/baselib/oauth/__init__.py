from JumpScale import j

def cb():
    from .OauthFactory import OauthFactory
    return OauthFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('oauth', cb)
