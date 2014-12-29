#!/usr/bin/env python
from JumpScale import j
import sys
import JumpScale.lib.diskmanager
import os
import JumpScale.baselib.netconfig
import netaddr
from libvirtutil import LibvirtUtil
import imp
import JumpScale.baselib.remote

"""
HRDIMAGE format
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
fabric.module=
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
        #self.gateway = "192.168.1.1"
        self.LibvirtUtil = LibvirtUtil()
        self.LibvirtUtil.basepath = self.vmpath


    def _getRootPath(self, name):
        return j.system.fs.joinPaths(self.vmpath, name)

    def loadImages(self):
        """
        walk over images & remember so we can use to create & manipulate machines
        """
        for image in j.system.fs.listDirsInDir(self.imagepath, recursive=False, dirNameOnly=True, findDirectorySymlinks=True):
            path = j.system.fs.joinPaths(self.imagepath, image, '%s.hrd' % image)
            hrd = j.core.hrd.get(path)
            self.images[image] = hrd

    def initPhysicalBridges(self, pubinterface="eth0"):
        """
        - names of bridges are brmgmt & brpub & brtmp(and are predefined)
        - brpub will be connected to e.g. eth0 on host and is for public traffic
        - brtmp is not connected to any physical device
        - brmgmt is not connected to physical device, it is being used for mgmt of vm 

        brmgmt is not connected to anything
            give static ip range 192.168.66.254/24 to bridge brmgmt (see self.ip_mgmt_range)
            will be used for internal mgmt purposes
        """
        print 'Creating physical bridges brpub, brmgmt and brtmp on the host...'
        j.system.netconfig.enableInterfaceBridge('brpub', pubinterface, True, False)
        j.system.netconfig.enableInterfaceBridgeStatic('brmgmt', ipaddr='192.168.66.254/24', start=True)
        j.system.netconfig.enableInterfaceBridgeStatic('brtmp')

    def initLibvirtNetowrk(self):
        print 'Creating libvirt networks brpub, brmgmt and brtmp...'
        networks = ('brmgmt', 'brpub', 'brtmp')
        for network in networks:
            j.system.platform.kvm.LibvirtUtil.createNetwork(network, network)

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
        return hrd.get("bootstrap.ip")

    def getConfig(self, name):
        configpath = j.system.fs.joinPaths(self.vmpath, name, "main.hrd")
        if not j.system.fs.exists(path=configpath):
            print 'Machine %s does not exist' % name
            return
        return j.core.hrd.get(path=configpath)

    def _getAllMachinesIps(self):
        """
        walk over all vm's, get config & read ip addr
        put them in dict      
        """
        ips = dict()
        for name in self._getAllVMs():
            hrd = self.getConfig(name)
            if hrd:
                ips[name] = hrd.get("bootstrap.ip")
        return ips

    def _getAllVMs(self):
        result = j.system.fs.listDirsInDir(self.vmpath, recursive=False, dirNameOnly=True, findDirectorySymlinks=True)
        result.remove('images')
        return result

    def _findFreeIP(self, name):
        """        
        find first ip addr which is free
        """
        ips=self._getAllMachinesIps()
        addr=[]
        for key,ip in ips.items():
            addr.append(int(ip.split(".")[-1].strip()))
        
        for i in range(2,252):
            if i not in addr:
                return '192.168.66.%s' % i

        j.events.opserror_critical("could not find free ip addr for KVM in 192.168.66.0/24 range","kvm.ipaddr.find")


    def create(self, name, baseimage, replace=True, description='', size=10, memory=512, cpu_count=1):
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

        @param size disk size in GBs
        @param memory memory size in MBs
        @param cpu_count is the number of vCPUs

        when replace then remove original image
        """
        if replace:
            if j.system.fs.exists(self._getRootPath(name)):
                print 'Machine %s already exists, will destroy and recreate...' % name
                self.destroy(name)
                j.system.fs.removeDirTree(self._getRootPath(name))
        j.system.fs.createDir(self._getRootPath(name))
        print 'Creating machine %s...' % name
        self.LibvirtUtil.create_node(name, baseimage, size=size, memory=memory, cpu_count=cpu_count)
        print 'Wrtiting machine HRD config file...'
        domain = self.LibvirtUtil.connection.lookupByName(name)
        imagehrd = self.images[baseimage]
        hrdfile = j.system.fs.joinPaths(self._getRootPath(name), 'main.hrd')
        # assume that login and passwd are provided in the image hrd config file
        hrdcontents = '''id=%s
name=%s
image=%s
ostype=%s
arch=%s
version=%s
description=%s
fabric.module=%s
bootstrap.ip=%s
bootstrap.login=%s
bootstrap.passwd=%s
bootstrap.type=ssh''' % (domain.UUIDString(), name, imagehrd.get('name'), imagehrd.get('ostype'), imagehrd.get('arch'), imagehrd.get('version'), description,
                        imagehrd.get('fabric.module'), imagehrd.get('bootstrap.ip'), imagehrd.get('bootstrap.login'), imagehrd.get('bootstrap.passwd'))
        j.system.fs.writeFile(hrdfile, hrdcontents)
        print 'Waiting for SSH connection to be ready...'
        if not j.system.net.waitConnectionTest(imagehrd.get('bootstrap.ip'), 22, 300):
            raise RuntimeError('SSH is not available after 5 minutes')
        self.pushSSHKey(name)
        public_ip = '37.50.210.16'
        print 'Setting network configuration on the guest, this might take some time...'
        self.setNetworkInfo(name, public_ip)
        print 'Machine %s created successfully' % name
        print 'Machine IP address is: %s' % self.getIp(name)

    def _getIdFromConfig(self, name):
        machine_hrd = self.getConfig(name)
        return machine_hrd.get('id')
        
    def destroyAll(self):
        print 'Destroying all created vmachines...'
        running, stopped = self.list()
        for item in running + stopped:
            self.destroy(item['name'])
        print 'Done'

    def destroy(self, name):
        print 'Destroying machine "%s"' % name
        machine_id = self._getIdFromConfig(name)
        self.LibvirtUtil.delete_machine(machine_id)
        
    def stop(self, name):
        print 'Stopping machine "%s"' % name
        machine_id = self._getIdFromConfig(name)
        self.LibvirtUtil.shutdown(machine_id)
        print 'Done'

    def start(self, name):
        print 'Starting machine "%s"' % name
        machine_id = self._getIdFromConfig(name)
        self.LibvirtUtil.create(machine_id, None)
        print 'Done'

    def setNetworkInfo(self, name, pubip):
        mgmtip = self._findFreeIP(name)
        capi = self._getSshConnection(name)
        machine_hrd = self.getConfig(name)
        setupmodule = self._getFabricModule(name)
        machine_hrd.set('bootstrap.ip', mgmtip)
        try:
            capi.fabric.api.execute(setupmodule.setupNetwork, ifaces={'eth0': (mgmtip, '255.255.255.0', '192.168.66.254'), 'eth1': (pubip, '255.255.255.0', '192.168.66.254')})
        except:
            if not j.system.net.waitConnectionTest(mgmtip, 22, 10):
                raise RuntimeError('Could not change machine ip address')
        finally:
            capi.fabric.network.disconnect_all()

    def networkSetPrivateVXLan(self, name, vxlanid, ipaddresses):
        #not to do now, phase 2
        raise RuntimeError("not implemented")

    def snapshot(self, name, snapshotname, disktype='all', snapshottype='external'):
        """
        take a snapshot of the disk(s)
        @param disktype = all,root,data1,data2
        #todo define naming convention for how snapshots are stored on disk
        """
        machine_hrd = self.getConfig(name)
        print 'Creating snapshot %s for machine %s' % (snapshotname, name)
        self.LibvirtUtil.snapshot(machine_hrd.get('id'), snapshotname, snapshottype=snapshottype)

    def deleteSnapshot(self, name, snapshotname):
        '''
        deletes a vmachine snapshot
        @param name: vmachine name
        @param snapshotname: snapshot name
        '''
        machine_hrd = self.getConfig(name)
        print 'Deleting snapshot %s for machine %s' % (snapshotname, name)
        self.LibvirtUtil.deleteSnapshot(machine_hrd.get('id'), snapshotname)

    def mountSnapshot(self,name,snapshotname,location="/mnt/1"):
        """
        try to mount the snapshotted disk to a location
        at least supported btrfs,ext234,ntfs,fat,fat32
        """

    def _getFabricModule(self, name):
        machine_hrd = self.getConfig(name)
        setipmodulename = machine_hrd.get('fabric.module')
        setupmodulepath = j.system.fs.joinPaths(self.imagepath, machine_hrd.get('image'), 'fabric', '%s.py' % setipmodulename)
        return imp.load_source(setipmodulename, setupmodulepath)

    def pushSSHKey(self, name):
        print 'Pushing SSH key to the guest...'
        privkeyloc="/root/.ssh/id_dsa"
        keyloc=privkeyloc + ".pub"
        if not j.system.fs.exists(path=keyloc):
            j.system.process.executeWithoutPipe("ssh-keygen -t dsa -f %s -N ''" % privkeyloc)
            if not j.system.fs.exists(path=keyloc):
                raise RuntimeError("cannot find path for key %s, was keygen well executed"%keyloc)            
        key=j.system.fs.fileGetContents(keyloc)
        # j.system.fs.writeFile(filename=path,contents="%s\n"%content)
        # path=j.system.fs.joinPaths(self._get_rootpath(name),"root",".ssh","known_hosts")
        # j.system.fs.writeFile(filename=path,contents="")
        c=j.remote.cuisine.api
        config = self.getConfig(name)
        c.fabric.api.env['password'] = config.get('bootstrap.passwd')
        c.fabric.api.env['connection_attempts'] = 5
        c.fabric.state.output["running"]=False
        c.fabric.state.output["stdout"]=False
        c.connect(config.get('bootstrap.ip'), config.get('bootstrap.login'))

        setupmodule = self._getFabricModule(name)
        if hasattr(setupmodule, 'pushSshKey'):
            c.fabric.api.execute(setupmodule.pushSshKey, sshkey=key)
        else:
            c.ssh_authorize("root", key)
        
        c.fabric.state.output["running"]=True
        c.fabric.state.output["stdout"]=True
        return key

    def _getSshConnection(self, name):
        capi = j.remote.cuisine.api
        capi.connect(self.getIp(name))
        return capi