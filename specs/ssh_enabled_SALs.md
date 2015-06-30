# SSH enabled SAL's

SAL = System Abstraction Layer
used in jumpscale to talk in a uniform way to a system
here the goal is to create a set of them working over ssh

- ssh enabled SAL's
    - all under j.ssh.$name
    - with factory classes
    - the first ones required are for openwrt and all start with uci_... 
        - uci stands for the configuration system used in openwrt 
    - each SSH enabled SAL does remote configuration of certain base components like dnsmasq, nginx, ...

```python
sshconnection = j.remote.cuisine.connect(...)
j.ssh.disklayout.get(sshconnection)
j.ssh.uci_dhcp.get(sshconnection) # this would be specific for openwrt
```  
the ssh connection is a fabric instance with key or passwd filled in & check done of working connection (there is already code for this in jumpscale)

## disk manager SAL (written for ubuntu)
* in python create a library which uses SSH to manipulate disks & partitions
* principles
 * we put .disk.hrd on each partition once configured 
```
protected: 1 or 0
type: root, data, tmp  
filesystem: btrfs, ext4, ntfs, fat32
mountpath: ...
devicename: ...
```
 * this .disk.hrd file is used to determine if partition can be removed or full disk (when no protected partitions)

### SAL API
```python
sshconnection = j.remote.cuisine.connect(...)
mgr = j.ssh.disklayout.get(sshconnection)
```
#### Manager API
##### getDisks()
```python
disks = mgr.getDisks()
"""Get list of all available disks on machine"""
```

#### Disk API
Each disk holds the following information:
- disk.partitions, list of partitions on that disk
- disk.name, device name (ex: /dev/sda)
- disk.size, disk size in bytes

##### disk.erase
```python
disk.erase(force=False)
"""
Clean up disk by deleting all non protected partitions
if force=True, delete ALL partitions included protected

:force: delete protected partitions, default=False
"""
```
##### disk.format
```python
disk.format(size, hrd)
"""
Create new partition and format it as configured in hrd file

:size: in bytes
:hrd: the disk hrd info

:return: new partition instance
Note:
hrd file must contain the following

filesystem                     = '<fs-type>'
mountpath                      = '<mount-path>'
protected                      = 0 or 1
type                           = data or root or tmp
"""
```

#### Partition API
Each disk has a list of attached partitions. The only way to create a new partition is to call `disk.format()` as explained above.
Each partition holds the following attributes

- partition.name, holds the device name (ex: /dev/sda1)
- partition.size, partition size in bytes
- partition.fstype, partition filesystem 
- partition.uuid, filesystem UUID
- partition.mountpoint, where the partition is mounted
- partition.hrd, the HRD instance used when creating the partition or None 

> partition.hrd can be `None`, in that case partition is considered `unmanaged` Which means partition is NOT created by the SAL. This type of partitions is considered 'protected' by default

> Partition attributes reflects the **real** state of the partition. For example, `mountpoint` will be set IF the partition is actually mounted, and is not related to the `mountpath` defined in the hrd file.

##### partition.delete
```python
partition.delete(force=False)
"""
Delete the partition

:force: Force delete protected partitions, default False
"""
```

##### partition.format
```python
partition.format()
"""
Reformat the partition according to HRD
"""
```

##### partition.mount
```python
parition.mount()
Mount partition to `mountpath` defined in HRD
```

##### partition.setAutoMount
```python
partition.setAutoMount(options='defaults', _dump=0, _pass=0)
"""
Configure partition auto mount `fstab` on `mountpath` defined in HRD
"""
```

##### partition.unsetAutoMount
```python
partition.unsetAutoMount()
"""
remote partition from fstab
"""
```

## DNS SAL (openwrt)
- configure dnsmasq, all over ssh
- limited support now e.g. A records
- work with factory class
    - wrt = j.ssh.openwrt.get(sshconnection)
    - wrt.dns.<method>()
- methods on dns SAL
    - records, dict with all A records in form {name: [ip, ...], ...}
    - erase(), removes all A records
    - addArecord(name, ip) add a new A record to DNS
    - removeArecord(name, ip=None) removes A record for name and IP. if ip is None, removes all A records for that name
    - commit(), apply changes and restart dnsmasq

## DHCP SAL (openwrt)
- configure dhcp server, all over ssh
- limited support now e.g. boot to pxe
- work with factory class
    - wrt = j.ssh.openwrt.get(sshconnection) 
    - wrt.dhcp.<method>
- methods on SAL
    - hosts, list of all static hosts.
    - erase(), removes all static hosts
    - addHost(name, mac, ip), add static host with name, mac and IP
    - removeHost(name), removes static host with name
    - pxe, configuration for pxe boot
    - pxe.filename,
    - pxe.serveraddress,
    - pxe.servername
    - pxe.options
    - commit(), apply changes and restart dnsmasq

## NGINX SAL
- configure nginx server, all over ssh
- limited support now e.g. just expose directory
- work with factory class
    - j.ssh.nginx.get(sshconnection,configpath="/etc/nginx") 
- methods on SAL
    - erase
    - add(...
    - delete(...
    - addconfig(... #push nginx configuration file to server and make sure it gets included when loading)
    - reload

## FTP server SAL (for openwrt)
- configure chosen ftp server, all over ssh
- limited support now e.g. just expose directory
- work with factory class
    - wrt = j.ssh.openwrt.get(sshconnection) 
    - wrt.ftp.<method>
> ftp configures PureFTP server, by default it uses unix authentication to serve users. So to access you need a user account on the openwrt device.
    - commit(), apply all ftp settings

## NFS server SAL (for openwrt)
- configure nfs server, all over ssh
- limited support now e.g. just expose directory
- work with factory class
    - j.ssh.uci_nfs.get(sshconnection) 
- methods on SAL
    - erase
    - add(...
    - delete(...
    - reload

## SSH server SAL
- configure ssh server, all over ssh
- work with factory class
    - j.ssh.server.get(sshconnection) 
- methods on SAL
    - erase
    - addkey(...
    - deletekey(...
    - disableNonKeyAccess(...
    - reload(...

## ufw SAL
- configure ufw firewall, all over ssh  - work with factory class
    - j.ssh.ufw.get(sshconnection) 
- methods on SAL
    - enabled, ufw status
    - rules, all configured rules
    - portOpen(port), short cut to open a port
    - portClose(port), short cut to close a port
    - addRule(action, source, destination), add a ufw rule
    - removeRule(rule), remove a ufw rule
    - reset(), drop all rules
    - commit(), apply changes to ufw
    
```python
ufw = j.ssh.ufw.get(connection)

ufw.enabled = False
ufw.reset()
ufw.addRule(ufw.ACTION_ALLOW_IN, 'any', '22/tcp')
ufw.enabled = True

ufw.commit()
```
## ucifw SAL = uci is config mgmt for openwrt
- configure firewall, all over ssh  - work with factory class
    - wrt = j.ssh.openwrt.get(sshconnection) 
- methods on SAL
    - portOpen()
    - portClose()
    - closeAll(exceptions=[22])

## ucinet SAL = uci enabled config mgmt for network
- configure uci based network configuration of openwrt, all over ssh    - work with factory class
    - wrt = j.ssh.openwrt.get(sshconnection)
    - wrt.network.<method>
- methods on SAL
    - nics, list of all available nics in the form [(dev, mac), ...]
    - interfaces, list of all configured virtual interfaces (as defined in open wrt UCI network)
    - addInterface(name), add new interface section
    - removeInterface(interface), remove interface section
    - find(nic), find all interfaces bind to the given nic name (basically finds sections with ifname==nic
    - commit(), apply changes and restart networking

### As an example to configure a static IP on eth0.
```python
wrt = j.ssh.openwrt.get(con)
inf = wrt.network.addInterface('any name goes here')
inf.ifname = 'eth0'
inf.proto = 'static'
inf.ipaddr = '1.2.3.4'
inf.netmask = '255.255.255.0'

wrt.network.commit()
```
## ubuntunet SAL = basic config mgmt for network for ubuntu
- like ucinet sal but now for ubuntu

## diskserver SAL 
- disk server is running rockstor & rockstor has rest api
- use aoe (ata over ethernet) to expose image file (be target)
- image file is hosted on filesystems in rockstor
    - this provides snapshotting, remote send, ...  - methods
    - vdisksList(storpath="/mnt/disktargets/")
        - see which images found which are exposed over aoe
    - vdiskCreate(storpath="/mnt/disktargets/mytest/disk1.aoe",size="10")
        - will create image file
        - will expose image file 
    - vdiskDelete(...
    - vdiskMount(...
        - mount locally 
