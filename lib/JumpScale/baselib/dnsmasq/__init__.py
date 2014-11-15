from JumpScale import j
from .dnsmasq import DNSMasq

j.base.loader.makeAvailable(j, 'tools')
j.tools.dnsmasq = DNSMasq()
