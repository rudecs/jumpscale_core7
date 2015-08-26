from JumpScale import j

j.application.start("pertests")

def singleLocalNodeTest():

    j.tools.perftesttools.init(monitorNodeIp="localhost",sshPort=22,redispasswd="",sshkey="")

    monitor=j.tools.perftesttools.getNodeMonitor()
    nas=j.tools.perftesttools.getNodeNas("localhost",22,nrdisks=0,fstype="xfs")
    host=j.tools.perftesttools.getNodeHost("localhost",22)

    nas.perftester.sequentialWriteReadBigBlock(nrfilesParallel=1)


def multiNodeMultDiskStripTest():

    """
    if you want to work from the monitoring vm: (remote option)
    on monitoring vm do, to make sure there are keys & ssh-agent is loaded
        js 'j.do.loadSSHAgent(createkeys=True)'
        #now logout & back login into that node, this only needs to happen once

    """
    mgmtkey="""
-----BEGIN DSA PRIVATE KEY-----
MIIBuwIBAAKBgQCUsI1t6Hxvgbhi+2iXEMa3a5IlVv9AQmdqzywo63KlJklRBV8B
sS/H0QaYE6msIQOucddUf3pxNCcI0YzXIc68ViQJ/N20tLKtKn1Cs+FAQG5HgAaB
tMqIEbODwEuQoz2sM7LETxxfyKHSpq+04eu10b8AQvBqbdonxkWXojtd8wIVAOab
J9nUbkvZvMxSnbn6CANzxtqrAoGAXsNJgp6RmDDgKu8Rw0I3Be75Sgu0fMXbmCCk
35lrmjAfpRyGrGoq6t2Xjsss/lznjJSr3TIEw4amSyIVBYooKsIcryFieCc3f9um
GmBNG6Rl8PMVjfLrvKB7uONdWsmKm/pUKOdTl8aQzp+ggEsi4od5zT3UCV9voFvj
/0MxewACgYA7oh7Z3OTmIPrvdoJDtYr3EjLmck6ohmO/EdljNLNVy1A8WiLau7rH
8WmgASC9ZKOt/+Y0DqIyJSnOZHy071yPoeIU1vSQ3UcWqeKjCWJvt+3mEAHof/Ol
DeKKIzr8KKGcUPROIQmy6fooeN4idnrtI9c2QXBNYHWqekHDuTpWZAIVAIaQPzv8
Ha5/w/N6XfqnrkCeqJ2i
-----END DSA PRIVATE KEY-----        
"""
    nrdisks=6

    j.tools.perftesttools.init(monitorNodeIp="192.168.103.252",sshPort=22,sshkey=mgmtkey)

    monitor=j.tools.perftesttools.getNodeMonitor()

    nasses=[]
    nasipaddr=["192.168.103.240","192.168.103.239","192.168.103.238","192.168.103.237"]
    #first init all nasses which takes some time
    for ipaddr in nasipaddr:
        nas=j.tools.perftesttools.getNodeNas(ipaddr,22,nrdisks=6,fstype="xfs")
        nasses.append(nas)
        nas.startMonitor(cpu=0,disks=1,net=0)

    #now start all the nas perftests
    for i in range(len(nasipaddr)):
        nas=nasses[i]
        #will write 3 parallel file sequential on each disk
        #each as has 6 disks, so 18 parallel writes
        nas.perftester.sequentialWriteReadBigBlock(nrfilesParallel=3)

    hosts=[]
    hostsip=["10.10.10.1","10.10.10.2","10.10.10.3","10.10.10.4"]
    for ipaddr in hostsip:
        host=j.tools.perftesttools.getNodeHost(ipaddr,22)
        hosts.append(host)
        host.startMonitor(cpu=1,disks=0,net=0)



# multiNodeMultDiskStripTest()
singleLocalNodeTest()
