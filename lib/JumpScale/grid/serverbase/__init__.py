from JumpScale import j


from .ServerBaseFactory import ServerBaseFactory

j.base.loader.makeAvailable(j, 'servers')
j.servers.base = ServerBaseFactory()
