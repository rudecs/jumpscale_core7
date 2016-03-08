__author__ = 'delandtj'

from .utils import *


class VXlan(object):
    def __init__(self,oid,backend='vxbackend'):
        def bytes(num):
            num = num + 256 >> 8
            return num >> 8, num & 0xFF

        self.id = NetID(oid)
        self.multicastaddr = '239.0.%s.%s' % bytes(self.id.oid)
        self.backend = backend
        self.name = 'vx-' + self.id.tostring()
    def create(self):
        createVXlan(self.name, self.id.oid, self.multicastaddr, self.backend)
    def destroy(self):
        destroyVXlan(self.name)
    def no6(self):
        disable_ipv6(self.name)
    def verify(self):
        pass

class Bridge(object):
    def __init__(self, name):
        self.name = name
    def create(self):
        createBridge(self.name)
    def destroy(self):
        destroyBridge(self.name)
    def connect(self,interface):
        connectIfToBridge(self.name,interface)
    def no6(self):
        disable_ipv6(self.name)


class VXBridge(Bridge):
    def __init__(self, oid):
        oid = NetID(oid)
        self.oid = oid
        self.name = 'space_' + oid.tostring()

    def listConnections(self):
        return listBridgeConnections(self.name)

class BondBridge(object):
    def __init__(self, name, interfaces, bondname=None, trunks=None):
        self.name = name
        self.interfaces = interfaces
        self.trunks = trunks
        if bondname is not None:
            self.bondname = "%s-Bond" % self.name
        else:
            self.bondname = bondname

    def create(self):
        createBridge(self.name)
        addBond(self.name, self.bondname, self.interfaces,trunks=self.trunks)

    def destroy(self):
        destroyBridge(self.name)


class NameSpace(object):
    def __init__(self, name):
        self.name = name
    def create(self):
        createNameSpace(self.name)
    def destroy(self):
        destroyNameSpace(self.name)
    def connect(self,interface):
        connectIfToNameSpace(self.name,interface)


class VXNameSpace(NameSpace):
    def __init__(self,oid):
        self.name = 'ns-' + oid.tostring()


class NetID(object):
    def __init__(self, oid):
        if isinstance(oid, basestring):
            self.oid = int(oid,16)
        elif isinstance(oid, NetID):
            self.oid = oid.oid
        else:
            self.oid = oid

    def tostring(self):
        # netidstring = str(hex(self.netid,16))[2:]
        oidstring = '%04x' % self.oid
        return oidstring


class VethPair(object):
    def __init__(self,oid):
        self.left = 'veth-left-%s' % oid.tostring()
        self.right = 'veth-right-%s' % oid.tostring()
    def create(self):
        createVethPair(self.left, self.right)
        # left has never an ip
        disable_ipv6(self.left)
    def destroy(self):
        destroyVethPair(self.left)

