# @ys boot/install system

- components
    - ssh server
    - pxe boot env (tftp, dhcp)
    - dns (by means of dnsmasq)
    - nfs, web & ftp server
    - hosts required ubuntu repositories
    - hosts 911 
    - create mini webservice (use swagger) 
- how to build this appliance
     - @ys
     - start from openwrt base image with SSH installed
     - @ys sshnode points to this openwrt
     - @ys bootnode (new @ys) (link to sshnode)
        - params: gridname, gridnr  (2bytes int translates to iprange as specified below e.g 256 : 255.1, e.g. 10: 0.10 ) 
        - install action: 
            - install all required components (see above)
            - configure dns, pxe, ...
            - put required config files on a git repo use @ys to have them locally on machine used to install bootnode from (use recipe)
            - use templates & scp to push them to the openwrt boot server
            - download (rsync?) required repo's & other images from central server(s)
       - implement the monitoring method to check the cifs, ftp, dns ...
       - configuration 
            - ip addr range: 10.$gridnr.$gridnrpart2.0/255
            - hostname: $gridname
            - dns: $cpuX.$gridname.aydo.com (X is 001,002, ... 011, ... 200)
            - ftp/web exposes /mnt/stor
            - std login/passwd $gridname:$gridnr for ftp shows stor
            - there is no private info on /mnt/stor 
- result
    - an openwrt virtual machine or physical small appliance using USB stick which can be used to boot/install a local network

## how to use this boot service

- all through @ys
- create racktivity @ys
    - params: ipaddr/passwd 
- create disklayout @ys
    - params
        - rootsize = 10  (10 gb is standard)
    - linked to sshnode  
    - method execute
        - use ssh to partition disks as required
        - use the disklayout SAL to erase & configure the disks
        - such a disklayout is specific per type of installation
- create node @ys to be used in combination with this boot/install server
    - params: 
        - name e.g. cpu001
        - nr in ip range e.g. 1, 
        - mac addr of first nic
        - protect yes or no (when protect a flag is set on root disk after install of system)
    - link to key to be used as root ssh key
    - link to disklayout &ys
    - install step 1
        - configure boot server to know about this node =   
        - configure DNS: A record cpu001 points to ip addr as specified (only use SSH for this to configure on bootserver)
    - install step 2 
        - configure boot server to boot this server in 911 mode
        - this happens through configuring dhcp & reloading dhcp
    - install step 3
        - find relevant racktivity node, use racktivity SAL to power off/on the required node(server)
        -  keep on pinging & then ssh test to see we can login to node 
        -  check this is a 911 node (hostname = 911)
        -  check mac addr of first nic= param (this to avoid mistakes!)
    - install step 4
        - call execute method on linked disklayout @ys
        - this will make sure that all non protected partitions are formatted & ready to be used
        - the disklayout can use a diskserver for disks (using AOE)
    - install step 5
        - call mount method on disklayout sal
        - expand required image coming from http on boot server onto root
    - install step 6
        - configure system with right SSH key
        - remove root access if no key or any other account access 
    - install step 7
        - configure dhcp on boot/install node to allow this node to boot from local disk
    - install step 8  
        - reboot 911
        - do ping/ssh test

# bootstrap principle for testlab

how to get a base to start from for further installation

- @ys sshkey
- @ys disklayout
- @ys diskserver node
    - are the 6 disk nodes
    - is using http://rockstor.com/ with AOE see sal above
    - put 6 disks in stripe in btrfs
    - expose virtual disks (images) over AOE (Ata Over Ethernet)
- @ys cpu node using the key & disk layout
    - result is a cpu node to which we have ssh access
    - our specific implementation of disklayout will use remote disks on diskserver when required
- at this point a node e.g. cpu node is configured & has ssh access & disks configured properly
- now use further @ys to configure required services
 
 ## example install
- 1 @YS configures 4 cpu nodes + 8 disks connected per cpu node, this is right configuration to test our first hyperconverged infrastructure, the result is 1 SSH key connection to all 4 cpu nodes
- management on MS1 through @ys

