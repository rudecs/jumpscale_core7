from JumpScale import j


from .GeventWSFactory import GeventWSFactory

j.base.loader.makeAvailable(j, 'servers')
j.servers.geventws = GeventWSFactory()
