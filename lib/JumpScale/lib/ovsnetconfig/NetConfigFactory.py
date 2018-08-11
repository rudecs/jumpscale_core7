#!/usr/bin/env python
import netaddr
import pprint
import os

from JumpScale import j
import VXNet.vxlan as vxlan
import VXNet.netclasses as netcl
from .VXNet.utils import addVlanPatch, createVethPair, ip_link_set
from JumpScale.core.system.fs import FileLock

class NetConfigFactory():

    def __init__(self):
        self._layout=None
        self.PHYSMTU = 2000 # will fit all switches


    def getConfigFromSystem(self,reload=False):
        """
        walk over system and get configuration, result is dict
        """
        if self._layout==None or reload:
            self._layout=vxlan.NetLayout()
            self._layout.load()
        # add_ips_to(self._layout)  #@todo fix
        return self._layout.nicdetail

    def _exec(self,cmd,failOnError=True):
        print(cmd)
        rc,out=j.system.process.execute(cmd,dieOnNonZeroExitCode=failOnError)
        return out

    def removeOldConfig(self):
        cmd="brctl show"
        for line in self._exec(cmd).split("\n"):
            if line.strip()=="" or line.find("bridge name")!=-1:
                continue
            name=line.split("\t")[0]
            self._exec("ip link set %s down"%name)
            self._exec("brctl delbr %s"%name)

        for intname,data in self.getConfigFromSystem(reload=True).items():
            if "PHYS" in data["detail"]:
                continue
            if intname =="ovs-system":
                continue
            self._exec("ovs-vsctl del-br %s"%intname,False)

        out=self._exec("virsh net-list",False)
        if out.find("virsh: not found")==-1:
            state="start"
            for line in out.split("\n"):
                if state=="found":
                    if line.strip()=="":
                        continue
                    line=line.replace("\t"," ")
                    name=line.split(" ")[0]
                    self._exec("virsh net-destroy %s"%name,False)
                    self._exec("virsh net-undefine %s"%name,False)

                if line.find("----")!=-1:
                    state="found"

        j.system.fs.writeFile(filename="/etc/default/lxc-net",contents="USE_LXC_BRIDGE=\"false\"",append=True) #@todo UGLY use editor !!!

        # Not used and expensive self.getConfigFromSystem(reload=True)

        j.system.fs.writeFile(filename="/etc/network/interfaces",contents="auto lo\n iface lo inet loopback\n\n")

    def initNetworkInterfaces(self):
        """
        Resets /etc/network/interfaces with a basic configuration
        """
        j.system.fs.writeFile(filename="/etc/network/interfaces",contents="auto lo\n iface lo inet loopback\n\n")

    def printConfigFromSystem(self):
        pprint.pprint(self.getConfigFromSystem())

    def newBridge(self,name,interface=None):
        """
        @param interface interface where to connect this bridge to
        """
        br=netcl.Bridge(name)
        br.create()
        if interface is not None:
            br.connect(interface)

    def newVlanBridge(self, name, parentbridge, vlanid, mtu=None):
        addVlanPatch(parentbridge, name, vlanid, mtu=mtu)

    def createExtNetwork(self, vlan):
        bridgename = self.getVlanBridge(vlan)
        nics = j.system.net.getNics()
        if bridgename not in nics:
            extbridge = 'ext-bridge'
            if extbridge not in nics:
                extbridge = 'backplane1'
            j.system.ovsnetconfig.newVlanBridge(bridgename, extbridge, vlan)
        return bridgename

    def ensureVXNet(self, networkid, backend):
        vxnet = vxlan.VXNet(networkid, backend)
        vxnet.innamespace=False
        vxnet.inbridge = True
        vxnet.apply()
        return vxnet

    def _generatenewdevname(self, prefix='veth'):
        length = 15 - len(prefix)
        devname = 'veth{}'.format(j.base.idgenerator.generateXCharID(length))
        while devname in j.system.net.getNics():
            devname = 'veth{}'.format(j.base.idgenerator.generateXCharID(length))
        return devname

    def connectInNameSpace(self, ovsbridge, namespace, ipaddress=None, gateway=None, name=None):
        namespace = netcl.NameSpace(namespace)
        bridge = netcl.Bridge(ovsbridge)
        namespace.create()

        iin = self._generatenewdevname()
        iout = self._generatenewdevname()
        createVethPair(iin, iout)
        namespace.connect(iin)
        bridge.connect(iout)
        if name:
            ip_link_set(iin, 'name {}'.format(name), namespace.name)
        else:
            name = iin
        ip_link_set(name, 'up', namespace.name)
        if ipaddress:
            self._exec('ip -n {} address add {} dev {}'.format(namespace.name, ipaddress, name))
        if gateway:
            self._exec('ip -n {} route add default via {}'.format(namespace.name, gateway))
        return name, iout

    def cleanupIfUnused(self, networkid):
        with FileLock('vxlan_%s' % networkid):
            bridge = netcl.VXBridge(networkid)
            connections = bridge.listConnections()
            if len(connections) > 1:
                return False
            else:
                vxlan = netcl.VXlan(networkid)
                vxlan.destroy()
                bridge.destroy()
                return True

    def getVlanBridge(self, vlan):
        if vlan is None or vlan == 0:
            bridgename = 'public'
        else:
            bridgename = 'ext-%04x' % vlan
        return bridgename

    def cleanupIfUnusedVlanBridge(self, bridgename=None, vlan=None):
        if bridgename is None and vlan is None:
            raise ValueError('Requires at least bridgename or vlan')
        if bridgename is None:
            bridgename = self.getVlanBridge(vlan)
        with FileLock('vlan_%s' % bridgename):
            bridge = netcl.Bridge(bridgename)
            connections = bridge.listConnections()
            if len(connections) > 1:
                return False
            else:
                for connection in connections:
                    parentbridge, vlan = connection.split('-')
                    bridge.removeInterface(connection)
                    pbridge = netcl.Bridge(parentbridge)
                    pbridge.removeInterface('{}-{}'.format(bridgename, vlan))
                bridge.destroy()

    def createVXLanBridge(self, networkid, backend,bridgename=None):
        """
        Creates a proper vxlan interface and bridge based on a backplane
        """
        networkoid = netcl.NetID(networkid)
        vxlan = netcl.VXlan(networkoid, backend)
        vxlan.create()
        vxlan.no6()
        bridge = netcl.Bridge(bridgename)
        bridge.create()
        bridge.connect(vxlan.name)
        return vxlan

    def getType(self,interfaceName):
        layout=self.getConfigFromSystem()
        if interfaceName not in layout:
            raise RuntimeError("cannot find interface %s"%interfaceName)
        interf=layout[interfaceName]
        if "type" in interf["params"]:
            return interf["params"]["type"]
        return None

    def setBackplaneDhcp(self,interfacename="eth0",backplanename="Public"):
        """
        DANGEROUS, will remove old configuration
        """
        C="""
auto $BPNAME
allow-ovs $BPNAME
iface $BPNAME inet dhcp
 dns-nameserver 8.8.8.8 8.8.4.4
 ovs_type OVSBridge
 ovs_ports $iname

allow-$BPNAME $iname
iface $iname inet manual
 ovs_bridge $BPNAME
 ovs_type OVSPort
 up ip link set $iname mtu $MTU
"""
        C=C.replace("$BPNAME", str(backplanename))
        C=C.replace("$iname", interfacename)
        C=C.replace("$MTU", str(self.PHYSMTU))

        ed=j.codetools.getTextFileEditor("/etc/network/interfaces")
        ed.setSection(backplanename,C)

    def setBackplaneNoAddress(self,interfacename="eth0",backplanename=1):
        """
        DANGEROUS, will remove old configuration
        """
        C="""
auto $BPNAME
allow-ovs $BPNAME
iface $BPNAME inet manual
  ovs_type OVSBridge
  ovs_ports eth7

allow-$BPNAME $iname
iface $iname inet manual
  ovs_bridge $BPNAME
  ovs_type OVSPort
  up ip link set $iname mtu $MTU
"""
        C=C.replace("$BPNAME", str(backplanename))
        C=C.replace("$iname", interfacename)
        C=C.replace("$MTU", str(self.PHYSMTU)) # strings here
        ed=j.codetools.getTextFileEditor("/etc/network/interfaces")
        ed.setSection(backplanename,C)

    def configureStaticAddress(self,interfacename="eth0",ipaddr="192.168.10.10/24",gw=None, mtu=None):
        """
        Configure a static address
        """
        C="""
auto $interface
allow-ovs $interface
iface $interface inet static
 address $ipbase
 netmask $mask
 $gw
 $mtu
"""
        n=netaddr.IPNetwork(ipaddr)

        C=C.replace("$interface", interfacename)
        C=C.replace("$ipbase", str(n.ip))
        C=C.replace("$mask", str(n.netmask))
        if gw:
            C=C.replace("$gw", "gateway %s"%gw)
        else:
            C=C.replace("$gw", "")

        if mtu:
            C=C.replace("$mtu", "post-up ip l set %s mtu %d" % (interfacename, mtu))
        else:
            C=C.replace("$mtu", "")

        ed=j.codetools.getTextFileEditor("/etc/network/interfaces")
        ed.setSection(interfacename,C)
        ed.save()


    def setBackplaneNoAddressWithBond(self,bondname, bondinterfaces,backplanename='backplane'):
        """
        DANGEROUS, will remove old configuration
        """
        C="""
auto $BPNAME
allow-ovs $BPNAME
iface $BPNAME inet manual
 ovs_type OVSBridge
 ovs_ports $bondname

allow-$BPNAME $bondname
iface $bondname inet manual
 ovs_bridge $BPNAME
 ovs_type OVSBond
 ovs_bonds $bondinterfaces
 ovs_options bond_mode=balance-tcp lacp=active bond_fake_iface=false other_config:lacp-time=fast bond_updelay=2000 bond_downdelay=400
 $disable_ipv6
"""
        interfaces = ''
        disable_ipv6 = ''
        for interface in bondinterfaces:
            interfaces += '%s ' % interface
            disable_ipv6 += 'pre-up ip l set %s mtu 2000 \n up sysctl -w net.ipv6.conf.%s.disable_ipv6=1 \n' % (interface, interface)
        C=C.replace("$BPNAME", str(backplanename))
        C=C.replace("$bondname", bondname)
        C=C.replace("$MTU", str(self.PHYSMTU))
        C=C.replace("$bondinterfaces" , interfaces)
        C=C.replace("$disable_ipv6" , disable_ipv6)

        ed=j.codetools.getTextFileEditor("/etc/network/interfaces")
        ed.setSection(backplanename,C)
        ed.save()




    def setBackplane(self,interfacename="eth0",backplanename=1,ipaddr="192.168.10.10/24",gw=""):
        """
        DANGEROUS, will remove old configuration
        """
        C="""
auto $BPNAME
allow-ovs $BPNAME
iface $BPNAME inet static
 address $ipbase
 netmask $mask
 dns-nameserver 8.8.8.8 8.8.4.4
 ovs_type OVSBridge
 ovs_ports $iname
 $gw

allow-$BPNAME $iname
iface $iname inet manual
 ovs_bridge $BPNAME
 ovs_type OVSPort
 up ip link set $iname mtu $MTU
"""
        n=netaddr.IPNetwork(ipaddr)
        C=C.replace("$BPNAME", str(backplanename))
        C=C.replace("$iname", interfacename)
        C=C.replace("$ipbase", str(n.ip))
        C=C.replace("$mask", str(n.netmask))
        C=C.replace("$MTU", str(self.PHYSMTU))
        if gw!="" and gw!=None:
            C=C.replace("$gw", "gateway %s"%gw)
        else:
            C=C.replace("$gw", "")

        ed=j.codetools.getTextFileEditor("/etc/network/interfaces")
        ed.setSection(backplanename,C)
        ed.save()

    def setBackplaneWithBond(self,bondname, bondinterfaces,backplanename='backplane',ipaddr="192.168.10.10/24",gw=""):
        """
        DANGEROUS, will remove old configuration
        """
        C="""
auto $BPNAME
allow-ovs $BPNAME
iface $BPNAME inet static
 address $ipbase
 netmask $mask
 dns-nameserver 8.8.8.8 8.8.4.4
 ovs_type OVSBridge
 ovs_ports $bondname
 $gw

allow-$BPNAME $bondname
iface $bondname inet manual
 ovs_bridge $BPNAME
 ovs_type OVSBond
 ovs_bonds $bondinterfaces
 ovs_options bond_mode=balance-tcp lacp=active bond_fake_iface=false other_config:lacp-time=fast bond_updelay=2000 bond_downdelay=400
 $disable_ipv6
"""
        n=netaddr.IPNetwork(ipaddr)
        interfaces = ''
        disable_ipv6 = ''
        for interface in bondinterfaces:
            interfaces += '%s ' % interface
            disable_ipv6 += 'pre-up ip l set %s mtu 2000 \n up sysctl -w net.ipv6.conf.%s.disable_ipv6=1 \n' % (interface, interface)
        C=C.replace("$BPNAME", str(backplanename))
        C=C.replace("$bondname", bondname)
        C=C.replace("$ipbase", str(n.ip))
        C=C.replace("$mask", str(n.netmask))
        C=C.replace("$MTU", str(self.PHYSMTU))
        if gw!="" and gw!=None:
            C=C.replace("$gw", "gateway %s"%gw)
        else:
            C=C.replace("$gw", "")
        C=C.replace("$bondinterfaces" , interfaces)
        C=C.replace("$disable_ipv6" , disable_ipv6)

        ed=j.codetools.getTextFileEditor("/etc/network/interfaces")
        ed.setSection(backplanename,C)
        ed.save()


    def applyconfig(self,interfacenameToExclude=None,backplanename=None):
        """
        DANGEROUS, will remove old configuration
        """
        for intname,data in self.getConfigFromSystem(reload=True).items():
            if "PHYS" in data["detail"] and intname!=interfacenameToExclude:
                self._exec("ip addr flush dev %s" % intname, False)
                self._exec("ip link set %s down"%intname,False)

        if backplanename!=None:
            self._exec("ifdown %s"%backplanename, failOnError=False)
            # self._exec("ifup %s"%backplanename, failOnError=True)

        #@todo need to do more checks here that it came up and retry couple of times if it did not
        #@ can do this by investigating self.getConfigFromSystem

        j.system.process.executeWithoutPipe("/etc/init.d/openvswitch-switch restart")


        print(self._exec("ip a", failOnError=True))
        print(self._exec("ovs-vsctl show", failOnError=True))

    def newBondedBackplane(self, name, interfaces, trunks=None):
        """
        Reasonable defaults  : mode=balance-tcp, lacp=active,fast, bondname=brname-Bond, all vlans allowed
        """
        br = netcl.BondBridge(name,interfaces)
        br.create()
