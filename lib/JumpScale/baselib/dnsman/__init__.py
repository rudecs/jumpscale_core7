from JumpScale import j

def cb():
    from .dnsFactory import DNSFactory
    return DNSFactory()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('dnsman', cb)
