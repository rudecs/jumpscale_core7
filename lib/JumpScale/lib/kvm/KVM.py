#!/usr/bin/env python
from JumpScale import j
import sys,time
import JumpScale.lib.diskmanager
import os
import JumpScale.baselib.netconfig
import netaddr
from libvirtutil import LibvirtUtil

HRDIMAGE="""
id=
name=
ostype = 
arch=
version=
description=

bootstrap.ip=
bootstrap.login=
bootstrap.passwd=
bootstrap.type=ssh

"""

class KVM(object):

    def __init__(self):
        """
        each vm becomes a subdir underneath the self.vmpath
        relevant info (which we need to remember, so which cannot be fetched from reality through libvirt) is stored in $vmpath/$name/vm.$name.hrd

        for networking in this first release we put 3 nics attached to std bridges
        - names of bridges are brmgmt & brpub & brtmp(and are predefined)
        - brpub will be connected to e.g. eth0 on host and is for public traffic
        - brtmp is not connected to any physical device
        - brmgmt is not connected to physical device, it is being used for mgmt of vm 

        images are always 2 files:
         $anyname.qcow2
         $anyname.hrd

        the hrd has all info relevant to vm (see HRDIMAGE constant)

        ostype is routeros,openwrt,ubuntu,windows, ...
        architecture i386,i64
        version e.g. 14.04
        name e.g. ourbase

        each image needs to have ssh agent installed and needs to be booted when machine starts & be configured using the params as specified

        """
        self.vmpath = "/mnt/vmstor/kvm"
        self.imagepath = "/mnt/vmstor/kvm/images"
        self.images = {}
        self.loadImages()
        self.ip_mgmt_range = "192.168.66.0/24" #used on brmgmt
        self.nameserver = "8.8.8.8"
        self.gateway = "192.168.1.1"
        self.LibvirtUtil = LibvirtUtil()
        self.LibvirtUtil.basepath = self.vmpath


    def _getRootPath(self, name):
        return j.system.fs.joinPaths(self.vmpath, name)

    def loadImages(self):
        """
        walk over images & remember so we can use to create & manipulate machines
        """
        for path in j.system.fs.listFilesInDir(self.imagepath, recursive=False, filter="*.hrd", listSymlinks=True):
            hrd = j.core.hrd.get(path)
            self.images[hrd.get("name")] = hrd

    def initbridges(self, pubinterface="eth0"):
        """
        - names of bridges are brmgmt & brpub & brtmp(and are predefined)
        - brpub will be connected to e.g. eth0 on host and is for public traffic
        - brtmp is not connected to any physical device
        - brmgmt is not connected to physical device, it is being used for mgmt of vm 

        brmgmt is not connected to anything
            give static ip range 192.168.66.254/24 to bridge brmgmt (see self.ip_mgmt_range)
            will be used for internal mgmt purposes
        """
        j.system.netconfig.enableInterfaceBridge('brpub', pubinterface, True, False)
        j.system.netconfig.enableInterfaceBridgeStatic('brmgmt', ipaddr='192.168.66.254/24', start=True)
        j.system.netconfig.enableInterfaceBridgeStatic('brtmp')

    def list(self):
        """
        names of running & stopped machines
        @return (running,stopped)
        """
        machines = self.LibvirtUtil.list_domains()
        running = [machine for machine in machines if machine['state'] == 1]
        stopped = [machine for machine in machines if machine['state'] == 5]
        return (running, stopped)

    def getIp(self, name):
        #info will be fetched from hrd in vm directory
        hrd = self.getConfig(name)
        return hrd.get("ipaddr")

    def getConfig(self, name):
        configpath = j.system.fs.joinPaths(self.vmpath, name, "main.hrd")
        if not j.system.fs.exists(path=configpath):
            raise RuntimeError('Machine %s does not exist' % name)
        return j.core.hrd.get(path=configpath)

    def _getAllMachinesIps(self):
        """
        walk over all vm's, get config & read ip addr
        put them in dict      
        """
        ips = dict()
        for name in self._getAllVMs():
            hrd = self.getConfig(name)
            ips[name] = hrd.get("ipaddr")
        return ips

    def _getAllVMs(self):
        return j.system.fs.listDirsInDir(self.vmpath, recursive=False, dirNameOnly=True, findDirectorySymlinks=True)

    def _findFreeIP(self, name):
        """        
        find first ip addr which is free
        """
        ips=self._getAllMachinesIps()
        if name in ips:
            return ips[name]
        else:
            addr=[]
            for key,ip in ips.items():
                addr.append(int(ip.split(".")[-1].strip()))
            
            for i in range(1,253):
                if i not in addr:
                    return i

        j.events.opserror_critical("could not find free ip addr for KVM in 192.168.66.0/24 range","kvm.ipaddr.find")


    def create(self, name, baseimage, start=False, replace=True):
        """
        create a KVM machine which inherits from a qcow2 image (so no COPY)

        always create a 2nd & 3e & 4th disk
        all on qcow2 format
        naming convention
        $vmpath/$name/tmp.qcow2
            $vmpath/$name/data1.qcow2
            $vmpath/$name/data2.qcow2            
        one is for all data other is for tmp

        when attaching to KVM: disk0=bootdisk, disk1=tmpdisk, disk2=datadisk1, disk3=datadisk2

        eth0 attached to brmgmt = for mgmt purposes
        eth1 to brpub
        eth2 to brtmp
        each machine gets an IP address from brmgmt range on eth0
        eth1 is attached to pubbridge
        eth2 is not connected to anything

        @param baseimage is name of the image used (see self.images)

        when replace then remove original image
        
        """
        j.system.fs.createDir(self._getRootPath(name))
        self.LibvirtUtil.create_node(name, baseimage)
        domain = self.LibvirtUtil.connection.lookupByName(name)
        imagehrd = self.images[baseimage]
        hrdfile = j.system.fs.joinPaths(self._getRootPath(name), 'main.hrd')
        # assume that login and passwd are provided in the image hrd config file
        hrdcontents = '''id=%s
name=%s
ostype=%s
arch=%s
version=%s
description=

bootstrap.ip=
bootstrap.login=%s
bootstrap.passwd=%s
bootstrap.type=ssh''' % (domain.UUIDString(), name, imagehrd.get('ostype'), imagehrd.get('arch'), imagehrd.get('version'),
                        imagehrd.get('bootstrap.login'), imagehrd.get('bootstrap.passwd'))
        j.system.fs.writeFile(hrdfile, hrdcontents)
        # if replace:
        #     if j.system.fs.exists(self._getMachinePath(name)):
        #         self.destroy(name)        
        # running,stopped=self.list()
        # machines=running+stopped

        # ipaddr=self._findFreeIP(name)

        # set the ip address inside the VM (NO DHCP !!!!)
        # use SSH to login to VM using info we know from image
        # depending type set the ip addr properly on eth1 (for management)
        # we will not set the ip addr for the other interfaces yet

        
        # ipaddrs=j.application.config.getDict("lxc.management.ipaddr")
        # if name in ipaddrs:
        #     ipaddr=ipaddrs[name]
        # else:
        #     #find free ip addr
        #     import netaddr
            
        #     existing=[netaddr.ip.IPAddress(item).value for item in  list(ipaddrs.values()) if item.strip()!=""]
        #     ip = netaddr.IPNetwork(j.application.config.get("lxc.management.iprange"))
        #     for i in range(ip.first+2,ip.last-2):
        #         if i not in existing:
        #             ipaddr=str(netaddr.ip.IPAddress(i))
        #             break
        #     ipaddrs[name]=ipaddr
        #     j.application.config.setDict("lxc.management.ipaddr",ipaddrs)

        # # mgmtiprange=j.application.config.get("lxc.management.iprange")
        # self.networkSetPrivateOnBridge( name,netname="mgmt0", bridge="mgmt", ipaddresses=["%s/24"%ipaddr]) #@todo make sure other ranges also supported

        #set ipaddr in hrd file
        # hrd=self.getConfig(name)
        # hrd.set("ipaddr",ipaddr)

        # if start:
        #     return self.start(name)

        # return ipaddr

    def _getIdFromConfig(self, name):
        machine_hrd = self.getConfig(name)
        return machine_hrd.get('id')
        
    def destroyAll(self):
        running, stopped = self.list()
        for item in running + stopped:
            self.destroy(item['name'])

    def destroy(self, name):
        machine_id = self._getIdFromConfig(name)
        self.LibvirtUtil.delete_machine(machine_id)
        
    def stop(self, name):
        machine_id = self._getIdFromConfig(name)
        self.LibvirtUtil.shutdown(machine_id)

    def start(self, name):
        machine_id = self._getIdFromConfig(name)
        self.LibvirtUtil.create(machine_id, None)

    def networkSetPublic(self, machinename,netname="pub0",pubips=[],bridge=None,gateway=None):
        """
        will have to use ssh
        """
        print(("set pub network %s on %s" %(pubips,machinename)))
        machine_cfg_file = j.system.fs.joinPaths('/var', 'lib', 'lxc', '%s%s' % (self._prefix, machinename), 'config')
        
        if not bridge:
            bridge = j.application.config.get('lxc.bridge.public')
        if not gateway:
            gateway = j.application.config.get('lxc.bridge.public.gw')
            if gateway=="":
                gateway=None

        config = '''
lxc.network.type = veth
lxc.network.flags = up
lxc.network.link = %s
lxc.network.name = %s
'''  % (bridge, netname)

#         notused="""
# #lxc.network.hwaddr = 00:FF:12:34:52:79
# #lxc.network.ipv4 = 192.168.22.1/24
# #lxc.network.ipv4.gateway = 192.168.22.254
# """

        ed=j.codetools.getTextFileEditor(machine_cfg_file)
        ed.setSection(netname,config)        

        #do not do will configure in fs of root of clone
        # for pubip in pubips:
        #     config += '''lxc.network.ipv4 = %s\n''' % pubip

        j.system.netconfig.setRoot(self._getRootPath(machinename)) #makes sure the network config is done on right spot
        for ipaddr in pubips:        
            j.system.netconfig.enableInterfaceStatic(dev=netname,ipaddr=ipaddr,gw=gateway,start=False)#do never start because is for lxc container, we only want to manipulate config
        j.system.netconfig.root=""#set back to normal


    def _getMachinePath(self,machinename,append=""):
        if machinename=="":
            raise RuntimeError("Cannot be empty")
        base = j.system.fs.joinPaths('/var', 'lib', 'lxc', '%s%s' % (self._prefix, machinename))
        if append!="":
            base=j.system.fs.joinPaths(base,append)
        return base

    def networkSetPrivateOnBridge(self, machinename,netname="dmz0", bridge=None, ipaddresses=["192.168.30.20/24"]):
        print(("set private network %s on %s" %(ipaddresses,machinename)))
        machine_cfg_file = self._getMachinePath(machinename,'config')
        
        config = '''
lxc.network.type = veth
lxc.network.flags = up
lxc.network.link = %s
lxc.network.name = %s
'''  % (bridge, netname)

        ed=j.codetools.getTextFileEditor(machine_cfg_file)
        ed.setSection(netname,config)

        if not bridge:
            bridge = j.application.config.get('lxc.bridge.public')        

        j.system.netconfig.setRoot(self._getRootPath(machinename)) #makes sure the network config is done on right spot
        for ipaddr in ipaddresses:        
            j.system.netconfig.enableInterfaceStatic(dev=netname,ipaddr=ipaddr,gw=None,start=False)
        j.system.netconfig.root=""#set back to normal


    def networkSetPrivateVXLan(self, name, vxlanid, ipaddresses):
        #not to do now, phase 2
        raise RuntimeError("not implemented")

    def _setConfig(self,name,parent):
        #now for LXC needs to be completely redone using LIBVIRT

        C="""
<volume>
        <name>{{diskname}}</name>
        <capacity unit='GB'>{{disksize}}</capacity>
        <allocation unit='GB'>{{disksize}}</allocation>
        <target>
            <path>{{diskname}}</path>
            <format type='qcow2'/>
            <compat>1.1</compat>
        </target>
        <backingStore>
            <format type='qcow2'/>
            <path>{{diskbasevolume}}</path>
        </backingStore>
 </volume>
        """


        print("SET CONFIG")
        base=self._getMachinePath(name)
        baseparent=self._getMachinePath(parent)
        machine_cfg_file = self._getMachinePath(name,'config')
        C="""
lxc.mount = $base/fstab
lxc.tty = 4
lxc.pts = 1024
lxc.arch = x86_64
lxc.cgroup.devices.deny = a
lxc.cgroup.devices.allow = c *:* m
lxc.cgroup.devices.allow = b *:* m
lxc.cgroup.devices.allow = c 1:3 rwm
lxc.cgroup.devices.allow = c 1:5 rwm
lxc.cgroup.devices.allow = c 5:1 rwm
lxc.cgroup.devices.allow = c 5:0 rwm
lxc.cgroup.devices.allow = c 1:9 rwm
lxc.cgroup.devices.allow = c 1:8 rwm
lxc.cgroup.devices.allow = c 136:* rwm
lxc.cgroup.devices.allow = c 5:2 rwm
lxc.cgroup.devices.allow = c 254:0 rm
lxc.cgroup.devices.allow = c 10:229 rwm
lxc.cgroup.devices.allow = c 10:200 rwm
lxc.cgroup.devices.allow = c 1:7 rwm
lxc.cgroup.devices.allow = c 10:228 rwm
lxc.cgroup.devices.allow = c 10:232 rwm
lxc.utsname = $name
lxc.cap.drop = sys_module
lxc.cap.drop = mac_admin
lxc.cap.drop = mac_override
lxc.cap.drop = sys_time
lxc.hook.clone = /usr/share/lxc/hooks/ubuntu-cloud-prep
lxc.rootfs = overlayfs:$baseparent/rootfs:$base/delta0
lxc.pivotdir = lxc_putold
"""        
        C=C.replace("$name",name)    
        C=C.replace("$baseparent",baseparent)
        C=C.replace("$base",base)
        j.system.fs.writeFile(machine_cfg_file,C)
        

    def snapshot(self,name,snapshotname,disktype="all"):
        """
        take a snapshot of the disk(s)
        @param disktype = all,root,data1,data2
        #todo define naming convention for how snapshots are stored on disk
        """

    def mountsnapshot(self,name,snapshotname,location="/mnt/1"):
        """
        try to mount the snapshotted disk to a location
        at least supported btrfs,ext234,ntfs,fat,fat32
        """