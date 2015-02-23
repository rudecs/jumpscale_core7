from JumpScale import j

def cb():
    from .dnsmasq import DNSMasq
    return DNSMasq()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('dnsmasq', cb)
