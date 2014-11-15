from JumpScale import j


from .QSocketServer import QSocketServer, QSocketServerFactory

j.base.loader.makeAvailable(j, 'system')
j.system.socketserver = QSocketServerFactory()
