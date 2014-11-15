from JumpScale import j


from .TornadoFactory import TornadoFactory

j.base.loader.makeAvailable(j, 'servers')
j.servers.tornado = TornadoFactory()
