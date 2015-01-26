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
import pynetlinux

"""
HRDIMAGE format
id=
name=
ostype = 
arch=
version=
description=
pub.ip=
bootstrap.ip=
bootstrap.login=
bootstrap.passwd=
bootstrap.type=ssh
fabric.module=
shell=
root.partitionnr=
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
        j.system.net.setBasicNetConfigurationBridgePub() #failsave method to introduce bridge to pub interface
        j.system.netconfig.enableInterfaceBridgeStatic('brmgmt', ipaddr='192.168.66.254/24', start=True)
        j.system.netconfig.enableInterfaceBridgeStatic('brtmp', start=True)

        # j.system.net.setBasicNetConfigurationBridgePub()
        if j.system.net.bridgeExists("brmgmt")==False:
            pynetlinux.brctl.addbr("brmgmt")
        br=pynetlinux.brctl.findbridge("brmgmt")        
        ip=br.get_ip()
        if ip!="192.168.66.254":  #there seems to be bug in this lib, will always be 0 the br.get_ip()
            br.set_ip("192.168.66.254")
            br.set_netmask(24)
        if br.is_up()==False:
            br.up()

        #tmp bridge
        if j.system.net.bridgeExists("brtmp")==False:
            pynetlinux.brctl.addbr("brtmp")
        br=pynetlinux.brctl.findbridge("brtmp")
        if br.is_up()==False:
            br.up()

    def initLibvirtNetwork(self):
        for brname in ("brmgmt", "brtmp", "brpub"):
            br=pynetlinux.brctl.findbridge(brname)
            if br.is_up()==False:
                br.up()

        print 'Creating libvirt networks brpub, brmgmt and brtmp...'
        networks = ('brmgmt', 'brpub', 'brtmp')
        for network in networks:
            if not self.LibvirtUtil.checkNetwork(network):
                j.system.platform.kvm.LibvirtUtil.createNetwork(network, network)
            else:
                print 'Virtual network "%s" is already there' % network

        for brname in ("brmgmt", "brtmp", "brpub"):
            br=pynetlinux.brctl.findbridge(brname)
            if br.is_up()==False:
                br.up()

    def initNattingRules(self):
        print('Initializing natting rule on the host on "brpub"...')
        cmd = "iptables -t nat -I POSTROUTING --out-interface brpub -j MASQUERADE"
        j.system.process.execute(cmd)
        cmd = "iptables -I FORWARD --in-interface brpub -j ACCEPT"
        j.system.process.execute(cmd)

    def list(self):
        """
        names of running & stopped machines
        @return (running,stopped)
        """
        machines = self.LibvirtUtil.list_domains()
        running = [machine for machine in machines if machine['state'] == 1]
        stopped = [machine for machine in machines if machine['state'] == 5 and j.system.fs.exists(j.system.fs.joinPaths(self.vmpath, machine['name']))]
        return (running, stopped)

    def listSnapshots(self, name):
        machine_hrd = self.getConfig(name)
        return [s['name'] for s in self.LibvirtUtil.listSnapshots(machine_hrd.get('id'))]

    def getIp(self, name):
        #info will be fetched from hrd in vm directory
        machine_hrd = self.getConfig(name)
        if machine_hrd:
            return machine_hrd.get("bootstrap.ip")

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
                ips[name] = hrd.get("bootstrap.ip"), hrd.get("pub.ip")
        return ips

    def _getAllVMs(self):
        result = j.system.fs.listDirsInDir(self.vmpath, recursive=False, dirNameOnly=True, findDirectorySymlinks=True)
        result.remove('images')
        return result

    def _findFreeIP(self, name):
        return self._findFreePubIP(name)

    def _findFreePubIP(self, name, pub=False):
        """        
        find first ip addr which is free
        """
        ips=self._getAllMachinesIps()
        addr=[]
        for key,ip in ips.items():
            if pub:
                addr.append(int(ip[1].split(".")[-1].strip()))
            else:
                addr.append(int(ip[0].split(".")[-1].strip()))
        
        for i in range(2,252):
            if i not in addr:
                if pub:
                    return '10.0.0.%s' % i
                else:
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
        self.initLibvirtNetwork()

        if replace:
            if j.system.fs.exists(self._getRootPath(name)):
                print 'Machine %s already exists, will destroy and recreate...' % name
                self.destroy(name)
                j.system.fs.removeDirTree(self._getRootPath(name))
        else:
            if j.system.fs.exists(self._getRootPath(name)):
                print 'Error creating machine "%s"' % name
                raise RuntimeError('Machine "%s" already exists, please explicitly specify replace=True(default) if you want to create a vmachine with the same name' % name)
        j.system.fs.createDir(self._getRootPath(name))
        print 'Creating machine %s...' % name
        try:
            self.LibvirtUtil.create_node(name, baseimage, size=size, memory=memory, cpu_count=cpu_count)
        except:
            print 'Error creating machine "%s"' % name
            print 'Rolling back machine creation...'
            return self.destroy(name)
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
root.partitionnr=%s
memory=%s
disk_size=%s
cpu_count=%s
shell=%s
fabric.module=%s
pub.ip=%s
bootstrap.ip=%s
bootstrap.login=%s
bootstrap.passwd=%s
bootstrap.type=ssh''' % (domain.UUIDString(), name, imagehrd.get('name'), imagehrd.get('ostype'), imagehrd.get('arch'), imagehrd.get('version'), description, imagehrd.get('root.partitionnr', '1'),
        memory, size, cpu_count, imagehrd.get('shell', ''), imagehrd.get('fabric.module'), imagehrd.get('pub.ip'), imagehrd.get('bootstrap.ip'), imagehrd.get('bootstrap.login'), imagehrd.get('bootstrap.passwd'))
        j.system.fs.writeFile(hrdfile, hrdcontents)
        print 'Waiting for SSH connection to be ready...'
        if not j.system.net.waitConnectionTest(imagehrd.get('bootstrap.ip'), 22, 300):
            print 'Rolling back machine creation...'
            self.destroy(name)
            raise RuntimeError('SSH is not available after 5 minutes')
        try:
            self.pushSSHKey(name)
        except:
            print 'Rolling back machine creation...'
            self.destroy(name)
            raise RuntimeError("Couldn't push SSH key to the guest")
        print 'Setting network configuration on the guest, this might take some time...'
        try:
            self.setNetworkInfo(name)
        except:
            print 'Rolling back machine creation...'
            self.destroy(name)
            raise RuntimeError("Couldn't configure guest network")
        print 'Machine %s created successfully' % name
        mgmt_ip = self.getIp(name)
        print 'Machine IP address is: %s' % mgmt_ip
        return mgmt_ip

    def destroyAll(self):
        print 'Destroying all created vmachines...'
        running, stopped = self.list()
        for item in running + stopped:
            self.destroy(item['name'])
        print 'Done'

    def destroy(self, name):
        print 'Destroying machine "%s"' % name
        try:
            self.LibvirtUtil.delete_machine(name)
        except:
            pass
        finally:
            j.system.fs.removeDirTree(self._getRootPath(name))
        
    def stop(self, name):
        print 'Stopping machine "%s"' % name
        try:
            self.LibvirtUtil.shutdown(name)
            print 'Done'
        except:
            pass

    def start(self, name):
        print 'Starting machine "%s"' % name
        try:
            self.LibvirtUtil.create(name, None)
            print 'Done'
        except:
            pass

    def setNetworkInfo(self, name):
        mgmtip = self._findFreeIP(name)
        public_ip = self._findFreePubIP(name, True)
        capi = self._getSshConnection(name)
        machine_hrd = self.getConfig(name)
        setupmodule = self._getFabricModule(name)
        machine_hrd.set('bootstrap.ip', mgmtip)
        machine_hrd.set('pub.ip', public_ip)
        try:
            capi.fabric.api.execute(setupmodule.setupNetwork, ifaces={'eth0': (mgmtip, '255.255.255.0', None), 'eth1': (public_ip, '255.255.255.0', '10.0.0.1')})
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
        print 'Creating snapshot %s for machine %s' % (snapshotname, name)
        machine_hrd = self.getConfig(name)
        try:
            self.LibvirtUtil.snapshot(machine_hrd.get('id'), snapshotname, snapshottype=snapshottype)
            print 'Done'
        except:
            pass

    def deleteSnapshot(self, name, snapshotname):
        '''
        deletes a vmachine snapshot
        @param name: vmachine name
        @param snapshotname: snapshot name
        '''
        machine_hrd = self.getConfig(name)
        print 'Deleting snapshot %s for machine %s' % (snapshotname, name)
        if snapshotname not in self.listSnapshots(name):
            print "Couldn't find snapshot %s for machine %s" % (snapshotname, name)
            return
        self.LibvirtUtil.deleteSnapshot(name, snapshotname)

    def mountSnapshot(self, name, snapshotname, location='/mnt/1', dev='/dev/nbd1', partitionnr=None):
        """
        try to mount the snapshotted disk to a location
        at least supported btrfs,ext234,ntfs,fat,fat32
        """
        machine_hrd = self.getConfig(name)
        if not machine_hrd:
            raise RuntimeError('Machine "%s" does not exist' % name)
        if snapshotname not in self.listSnapshots(name):
            raise RuntimeError('Machine "%s" does not have a snapshot named "%s"' % (name, snapshotname))
        print('Mounting snapshot "%s" of mahcine "%s" on "%s"' % (snapshotname, name, location))
        if not j.system.fs.exists(location):
            print('Location "%s" does not exist, it will be created' % location)
            j.system.fs.createDir(location)
        print('Device %s will be used, freeing up first...' % dev)
        j.system.process.execute('modprobe nbd max_part=8')
        self._cleanNbdMount(location, dev)
        qcow2_images = j.system.fs.listFilesInDir(j.system.fs.joinPaths(self.vmpath, name), filter='*.qcow2')
        snapshot_path = None
        for qi in qcow2_images:
            if snapshotname in qi:
                snapshot_path = qi
                break
        if not snapshot_path:
            raise RuntimeError('Could not find snapshot "%s" path' % snapshotname)
        j.system.process.execute('qemu-nbd --connect=%s %s' % (dev, snapshot_path))
        if not partitionnr:
            partitionnr = machine_hrd.get('root.partitionnr', '1')
        j.system.process.execute('mount %sp%s %s' % (dev, partitionnr, location))
        print('Snapshot "%s" of mahcine "%s" was successfully mounted on "%s"' % (snapshotname, name, location))

    def unmountSnapshot(self, location='/mnt/1', dev='/dev/nbd1'):
        self._cleanNbdMount(location, dev)

    def _cleanNbdMount(self, location, dev):
        print('Unmounting location "%s"' % location)
        try:
            j.system.process.execute('umount %s' % location)
        except:
            print('location "%s" is already unmounted' % location)
        print('Disconnecting dev "%s"' % dev)
        j.system.process.execute('qemu-nbd -d %s' % dev)

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

    def execute(self, name, cmd, sudo=False):
        rapi = self._getSshConnection(name)
        machine_hrd = self.getConfig(name)
        if machine_hrd:
            shell = machine_hrd.get('shell', '/bin/bash -l -c')
            user = machine_hrd.get('bootstrap.login', 'root')
            with rapi.fabric.api.settings(shell=shell, user=user):
                if not sudo:
                    return rapi.run(cmd, shell=shell)
                else:
                    return rapi.sudo(cmd, shell=shell)
        else:
            raise RuntimeError('Machine "%s" does not exist' % name)