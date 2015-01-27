

import time
import socket
import re

from JumpScale import j

IPBLOCKS = re.compile("(^|\n)(?P<block>\d+:.*?)(?=(\n\d+)|$)", re.S)
IPMAC = re.compile("^\s+link/\w+\s+(?P<mac>(\w+:){5}\w{2})", re.M)
IPIP = re.compile("^\s+inet\s(?P<ip>(\d+\.){3}\d+)/(?P<cidr>\d+)", re.M)
IPNAME = re.compile("^\d+: (?P<name>.*?)(?=:)", re.M)

def parseBlock(block):
    result = {'ip': [], 'cidr': [], 'mac': '', 'name': ''}
    for rec in (IPMAC, IPNAME):
        match = rec.search(block)
        if match:
            result.update(match.groupdict())
    for mrec in (IPIP, ):
        for m in mrec.finditer(block):
            for key, value in list(m.groupdict().items()):
                result[key].append(value)
    return result

def getNetworkInfo():
    exitcode,output = j.system.process.execute("ip a", outputToStdout=False)
    for m in IPBLOCKS.finditer(output):
        block = m.group('block')
        yield parseBlock(block)

class SystemNet:

    def __init__(self):
        self._windowsNetworkInfo = None

    def tcpPortConnectionTest(self,ipaddr,port, timeout=None):
        conn = None
        try:
            conn=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if timeout:
                conn.settimeout(timeout)
            try:
                conn.connect((ipaddr,port))
            except:
                return False
        finally:
            if conn:
                conn.close()
        return True
        
    def waitConnectionTest(self,ipaddr,port,timeout):
        """
        will return false if not successfull (timeout)
        """
        j.logger.log("test tcp connection to '%s' on port %s"%(ipaddr,port))
        if ipaddr.strip()=="localhost":
            ipaddr="127.0.0.1"
        port=int(port)
        start=j.base.time.getTimeEpoch()
        now=start
        remainingtime = (timeout - (now - start)) or 1
        while remainingtime > 0:
            if j.system.net.tcpPortConnectionTest(ipaddr,port, remainingtime):
                return True
            time.sleep(0.1)
            now=j.base.time.getTimeEpoch()
            remainingtime = (timeout - (now - start)) or 1
        return False

    def waitConnectionTestStopped(self,ipaddr,port,timeout):
        """
        will test that port is not active
        will return false if not successfull (timeout)
        """
        j.logger.log("test tcp connection to '%s' on port %s"%(ipaddr,port))
        if ipaddr.strip()=="localhost":
            ipaddr="127.0.0.1"
        port=int(port)
        start=j.base.time.getTimeEpoch()
        now=start
        while now<start+timeout:
            if j.system.net.tcpPortConnectionTest(ipaddr,port, 1)==False:
                return True
            now=j.base.time.getTimeEpoch()
        return False

    def checkUrlReachable(self, url):
        """
        raise operational critical if unreachable
        return True if reachable
        """
        # import urllib.request, urllib.parse, urllib.error
        try:
            import urllib
        except:
            import urllib.parse as urllib

        try:
            code = urllib.request.urlopen(url).getcode()
        except Exception:
            j.errorconditionhandler.raiseOperationalCritical("Url %s is unreachable" % url)
        
        if code != 200:
            j.logger.setLogTargetLogForwarder()
            j.errorconditionhandler.raiseOperationalCritical("Url %s is unreachable" % url)
        return True


    def checkListenPort(self, port):
        """
        Check if a certain port is listening on the system.

        @param port: sets the port number to check
        @return status: 0 if running 1 if not running
        """
        if port >65535 or port <0 :
            raise ValueError("Port cannot be bigger then 65535 or lower then 0")

        j.logger.log('Checking whether a service is running on port %d' % port, 8)

        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            # netstat: n == numeric, -t == tcp, -u = udp, l= only listening, p = program
            command = "netstat -ntulp | grep ':%s '" % port
            # raise RuntimeError("stop")
            (exitcode, output) = j.system.process.execute(command, dieOnNonZeroExitCode=False,outputToStdout=False)
            return exitcode == 0
        elif j.system.platformtype.isSolaris() or j.system.platformtype.isDarwin():
            command = "netstat -an -f inet"
            (exitcode, output) = j.system.process.execute(command, dieOnNonZeroExitCode=False,outputToStdout=False)
            for line in output.splitlines():
                match = re.match(".*\.%s .*\..*LISTEN"%port, line)
                if match:
                    return True
            # No ipv4? Then check ipv6
            command = "netstat -an -f inet6"
            (exitcode, output) = j.system.process.execute(command, dieOnNonZeroExitCode=False,outputToStdout=False)
            for line in output.splitlines():
                match = re.match(".*\.%s .*\..*LISTEN"%port, line)
                if match:
                    return True
            return False
        elif j.system.platformtype.isWindows():
            # We use the GetTcpTable function of the Windows IP Helper API (iphlpapi.dll)
            #
            # Parameters of GetTcpTable:
            #    - A buffer receiving the table.
            #    - An integer indicating the length of the buffer. This value will be overwritten with the required buffer size, if the buffer isn't large enough.
            #    - A boolean indicating if the table should be sorted.
            #
            # Microsoft reference: http://msdn2.microsoft.com/en-us/library/aa366026(VS.85).aspx
            # Python example code: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/392572

            import ctypes, socket
            DWORD = ctypes.c_ulong
            MIB_TCP_STATE_LISTEN = 2
            dwSize = DWORD(0)

            # Retrieve the size of the TCP table, to create a structure with the right size.
            # We do this by calling the GetTcpTable function and passing an empty buffer.
            # Because the buffer is too small, the dwSize variable will be overwritten with the required buffer size.
            ctypes.windll.iphlpapi.GetTcpTable("", ctypes.byref(dwSize), 0)

            # Define MIB (Management Information Base) classes
            class MIB_TCPROW(ctypes.Structure):
                _fields_ = [('dwState', DWORD),
                            ('dwLocalAddr', DWORD),
                            ('dwLocalPort', DWORD),
                            ('dwRemoteAddr', DWORD),
                            ('dwRemotePort', DWORD)]

            class MIB_TCPTABLE(ctypes.Structure):
                _fields_ = [('dwNumEntries', DWORD),
                            ('table', MIB_TCPROW * dwSize.value)]

            tcpTable = MIB_TCPTABLE()  # Initialize the buffer that will retrieve the TCP table
            tcpTable.dwNumEntries = 0

            # Call the GetTcpTable function again, but now with a buffer that's large enough. The TCP table will be written in the buffer.
            retVal = ctypes.windll.iphlpapi.GetTcpTable(ctypes.byref(tcpTable), ctypes.byref(dwSize), 0)
            if not retVal == 0:
                raise RuntimeError("j.system.net.checkListenPort: The function iphlpapi.GetTcpTable returned error number %s"%retVal)

            for i in range(tcpTable.dwNumEntries):  # We can't iterate over the table the usual way as tcpTable.table isn't a Python table structure.
                tcpState = tcpTable.table[i].dwState
                tcpLocalPort = socket.ntohs(tcpTable.table[i].dwLocalPort) # socket.ntohs() convert a 16-bit integer from network to host byte order.
                if tcpState == MIB_TCP_STATE_LISTEN and tcpLocalPort == port:
                    return True
            return False # The port is not in a listening state.

        else:
            raise RuntimeError("This platform is not supported in j.system.net.checkListenPort()")

    def getNameServer(self):
        """Returns the first nameserver IP found in /etc/resolv.conf

        Only implemented for Unix based hosts.

        @returns: Nameserver IP
        @rtype: string

        @raise NotImplementedError: Non-Unix systems
        @raise RuntimeError: No nameserver could be found in /etc/resolv.conf
        """
        if j.system.platformtype.isUnix():
            nameserverlines = j.codetools.regex.findAll(
            "^\s*nameserver\s+(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\s*$",
            j.system.fs.fileGetContents('/etc/resolv.conf'))

            if not nameserverlines:
                raise RuntimeError('No nameserver found in /etc/resolv.conf')

            nameserverline = nameserverlines[0]
            return nameserverline.strip().split(' ')[-1]
        elif j.system.platformtype.isWindows():
            import wmi
            w=wmi.WMI()
            for nicCfg in w.Win32_NetworkAdapterConfiguration():
                if nicCfg.DNSServerSearchOrder:
                    return str(nicCfg.DNSServerSearchOrder[0])
        else:
            raise NotImplementedError('This function is only supported on Unix/Windows systems')

    def getIpAddresses(self,up=False):
        if j.system.platformtype.isLinux():
            result = list()
            for ipinfo in getNetworkInfo():
                result.extend(ipinfo['ip'])
            return result
        else:
            nics=self.getNics(up)
            result=[]
            for nic in nics:
                ipTuple = self.getIpAddress(nic)
                if ipTuple: # if empty array skip
                    result.extend([ ip[0] for ip in ipTuple])
            return result
    
    def checkIpAddressIsLocal(self,ipaddr):
        if ipaddr.strip() in self.getIpAdresses():
            return True
        else:
            return False

    def enableProxy(self):
        maincfg = j.config.getConfig('main')
        if 'proxy' in maincfg:
            import os, urllib.request, urllib.error, urllib.parse
            proxycfg = maincfg['proxy']
            proxyserver = proxycfg['server']
            params = ""
            proxyuser =  proxycfg.get('user')
            if proxyuser:
                params += proxyuser
                proxypassword = proxycfg.get('password')
                if proxypassword:
                    params += ":%s" % proxypassword
                params += "@"
            params += proxyserver
            if j.system.platformtype.isUnix():
                os.environ['http_proxy'] = proxyserver
            proxy_support = urllib.request.ProxyHandler()
            opener = urllib.request.build_opener(proxy_support)
            urllib.request.install_opener(opener)
    
    def getNics(self,up=False):
        """ Get Nics on this machine
        Works only for Linux/Solaris systems
        @param up: only returning nics which or up
        """
        regex = ''
        output = ''
        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            exitcode,output = j.system.process.execute("ip l", outputToStdout=False)
            if not up:
                regex = "^\d+:\s(?P<name>[\w\d\-]*):.*$"
            else:
                regex = "^\d+:\s(?P<name>[\w\d\-]*):\s<.*UP.*>.*$"
            return list(set(re.findall(regex,output,re.MULTILINE)))
        elif j.system.platformtype.isSolaris():
            exitcode,output = j.system.process.execute("ifconfig -a", outputToStdout=False)
            if up:
                regex = "^([\w:]+):\sflag.*<.*UP.*>.*$"
            else:
                regex = "^([\w:]+):\sflag.*$"
            nics = set(re.findall(regex,output,re.MULTILINE))
            exitcode,output = j.system.process.execute("dladm show-phys", outputToStdout=False)
            lines = output.splitlines()
            for line in lines[1:]:
                nic = line.split()
                if up:
                    if nic[2] == 'up':
                        nics.add(nic[0])
                else:
                    nics.add(nic[0])
            return list(nics)
        elif j.system.platformtype.isWindows():
            import wmi
            w = wmi.WMI()
            return [ "%s:%s" %(ad.index,str(ad.NetConnectionID)) for ad in w.Win32_NetworkAdapter() if ad.PhysicalAdapter and ad.NetEnabled]
        else:
            raise RuntimeError("Not supported on this platform!")

    def getNicType(self,interface):
        """ Get Nic Type on a certain interface
        @param interface: Interface to determine Nic type on
        @raise RuntimeError: On linux if ethtool is not present on the system
        """
        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            output=''
            if j.system.fs.exists("/sys/class/net/%s"%interface):
                output = j.system.fs.fileGetContents("/sys/class/net/%s/type"%interface)
            if output.strip() == "32":
                return "INFINIBAND"
            else:
                if j.system.fs.exists('/proc/net/vlan/%s'%(interface)):
                    return 'VLAN'
                exitcode,output = j.system.process.execute("which ethtool", False, outputToStdout=False)
                if exitcode != 0:
                    raise RuntimeError("Ethtool is not installed on this system!")
                exitcode,output = j.system.process.execute("ethtool -i %s"%(interface),False,outputToStdout=False)
                if exitcode !=0:
                    return 'VIRTUAL'
                match = re.search("^driver:\s+(?P<driver>\w+)\s*$",output,re.MULTILINE)
                if match and match.group("driver") == "tun" :
                    return "VIRTUAL"
                if match and match.group("driver") == "bridge" :
                    return "VLAN"
                return "ETHERNET_GB"
        elif j.system.platformtype.isSolaris():
            command = "ifconfig %s"%interface
            exitcode,output = j.system.process.execute(command, outputToStdout=False, dieOnNonZeroExitCode=False)
            if exitcode != 0:
                # temporary plumb the interface to lookup its mac
                j.logger.log("Interface %s is down. Temporarily plumbing it to be able to lookup its nic type" % interface, 1)
                j.system.process.execute('%s plumb' % command, outputToStdout=False)
                (exitcode, output) = j.system.process.execute(command, outputToStdout=False)
                j.system.process.execute('%s unplumb' % command, outputToStdout=False)
            if output.find("ipib") >=0:
                return "INFINIBAND"
            else:
                #work with interfaces which are subnetted on vlans eq e1000g5000:1
                interfacepieces = interface.split(':')
                interface = interfacepieces[0]
                match = re.search("^\w+?(?P<interfaceid>\d+)$",interface,re.MULTILINE)
                if not match:
                    raise ValueError("Invalid interface %s"%(interface))
                if len(match.group('interfaceid')) >= 4:
                    return "VLAN"
                else:
                    if len(interfacepieces) > 1:
                        return "VIRTUAL"
                    else:
                        return "ETHERNET_GB"
        elif j.system.platformtype.isWindows():
            if j.system.net.getVlanTagFromInterface(interface) > 0:
                return "VLAN"
            else:
                import wmi
                w = wmi.WMI()
                NICIndex = interface.split(":")[0]
                nic = w.Win32_NetworkAdapter(index=NICIndex)[0]
                if hasattr(nic, 'AdapterTypeId'):
                    if nic.AdapterTypeId == 0:
                        return "ETHERNET_GB"
                    elif nic.AdapterTypeId == 15:
                        return "VIRTUAL"
                    else:
                        return "UNKNOWN"
                else:
                    return "UNKNOWN"
        else:
            raise RuntimeError("Not supported on this platform!")

    def getVlanTag(self,interface,nicType=None):
        """Get VLan tag on the specified interface and vlan type"""
        if nicType == None:
            nicType=j.system.net.getNicType(interface)
        if nicType == "INFINIBAND" or nicType=="ETHERNET_GB" or nicType == "VIRTUAL":
            return "0"
        if j.system.platformtype.isLinux():
            #check if its a vlan
            vlanfile = '/proc/net/vlan/%s'%(interface)
            if j.system.fs.exists(vlanfile):
                return j.system.net.getVlanTagFromInterface(interface)
            bridgefile = '/sys/class/net/%s/brif/'%(interface)
            for brif in j.system.fs.listDirsInDir(bridgefile):
                brif = j.system.fs.getBaseName(brif)
                vlanfile = '/proc/net/vlan/%s'%(brif)
                if j.system.fs.exists(vlanfile):
                    return j.system.net.getVlanTagFromInterface(brif)
            return "0"
        elif j.system.platformtype.isSolaris() or j.system.platformtype.isWindows():
            return j.system.net.getVlanTagFromInterface(interface)
        else:
            raise RuntimeError("Not supported on this platform!")

    def getVlanTagFromInterface(self,interface):
        """Get vlan tag from interface
        @param interface: string interface to get vlan tag on
        @rtype: integer representing the vlan tag
        """
        if j.system.platformtype.isLinux():
            vlanfile = '/proc/net/vlan/%s'%(interface)
            if j.system.fs.exists(vlanfile):
                content = j.system.fs.fileGetContents(vlanfile)
                match = re.search("^%s\s+VID:\s+(?P<vlantag>\d+)\s+.*$"%(interface),content,re.MULTILINE)
                if match:
                    return match.group('vlantag')
                else:
                    raise ValueError("Could not find vlantag for interface %s"%(interface))
            else:
                raise ValueError("This is not a vlaninterface %s"%(interface))
        elif j.system.platformtype.isSolaris():
            #work with interfaces which are subnetted on vlans eq e1000g5000:1
            interface = interface.split(':')[0]
            match = re.search("^\w+?(?P<interfaceid>\d+)$",interface,re.MULTILINE)
            if not match:
                raise ValueError("This is not a vlaninterface %s"%(interface))
            return int(match.group('interfaceid'))/1000
        elif j.system.platformtype.isWindows():
            import wmi
            vir = wmi.WMI(namespace='virtualization')
            mac = j.system.net.getMacAddress(interface)
            mac = mac.replace(":","")
            dynFor = vir.Msvm_DynamicForwardingEntry(elementname=mac)
            return dynFor[0].VlanId if dynFor else 0

    def getReachableIpAddress(self, ip, port):
        """Returns the first local ip address that can connect to the specified ip on the specified port"""
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((ip, port))
        except:
            raise RuntimeError("Cannot connect to %s:%s, check network configuration"%(ip,port))
        return s.getsockname()[0]

    def getDefaultIPConfig(self):
        ipaddr=self.getReachableIpAddress("8.8.8.8",22)
        for item in j.system.net.getNetworkInfo():
            for ipaddr2 in item["ip"]:
                # print "%s %s"%(ipaddr2,ipaddr)
                if str(ipaddr)==str(ipaddr2):
                    return item["name"],ipaddr

    def bridgeExists(self,bridgename):
        cmd="brctl show"
        rc,out,err=j.do.execute(cmd,outputStdout=False)
        for line in out.split("\n"):
            if line.lower().startswith(bridgename):
                return True
        return False

    def resetDefaultGateway(self,gw):
        def gwexists():
            cmd="ip r"
            rc,out,err=j.do.execute(cmd,outputStdout=False)
            for line in out.split("\n"):
                if line.lower().startswith("default"):
                    return True
            return False
        def removegw():
            cmd="ip route del 0/0"
            rc,out,err=j.do.execute(cmd,outputStdout=False,outputStderr=False,dieOnNonZeroExitCode=False)

        removegw()            
        couter=0
        while gwexists():
            removegw()
            time.sleep(1)
            print("try to delete def gw")
            counter+=1
            if counter>10:
                raise RuntimeError("cannot delete def gw")

        cmd='route add default gw %s'%gw
        j.do.execute(cmd)


    def setBasicNetConfiguration(self,interface="eth0",ipaddr=None,gw=None,mask=24,config=True):
        """
        @param config if True then will be stored in linux configuration files
        """
        import pynetlinux

        import JumpScale.baselib.netconfig
        j.system.netconfig.reset(True)        

        if ipaddr==None or gw == None:
            j.events.inputerror_critical("Cannot configure network when ipaddr or gw not specified","net.config")

        if pynetlinux.brctl.findbridge("brpub")<>None:
            print "found brpub, will try to bring down."
            i=pynetlinux.brctl.findbridge("brpub")
            i.down()
            counter=0
            while i.is_up() and counter<10:
                i.down()
                time.sleep(1)
                counter+=1
                print "waiting for bridge:brpub to go down"
        
        i=pynetlinux.ifconfig.findif(interface)
        if i<>None:            
            print "found %s, will try to bring down."%interface
            i.down()
            counter=0
            while i.is_up() and counter<10:
                i.down()
                time.sleep(1)
                counter+=1
                print "waiting for interface:%s to go down"%interface
        
        if config:
            import JumpScale.baselib.netconfig
            j.system.netconfig.enableInterfaceStatic(dev=interface,ipaddr="%s/%s"%(ipaddr,mask),gw=gw,start=True)
        else:
            print "set ipaddr:%s"%ipaddr
            i.set_ip(ipaddr)
            print "set mask:%s"%mask
            i.set_netmask(mask)
            print "bring interface up"
            i.up()

        while i.is_up()==False:
            i.up()
            time.sleep(1)
            print "waiting for interface:%s to go up"%interface 

        print "interface:%s up"%interface

        print "check can reach default gw:%s"%gw
        if not j.system.net.pingMachine(gw):
            j.events.opserror_critical("Cannot get to default gw, network configuration did not succeed for %s %s/%s -> %s"%(interface,ipaddr,mask,gw))
        print "gw reachable"

        self.resetDefaultGateway(gw)
        print "default gw up:%s"%gw

    def removeNetworkFromInterfaces(self,network="192.168.1"):
        for item in j.system.net.getNetworkInfo():
            for ip in item["ip"]:
                if ip.startswith(network):
                    #remove ip addr from this interface
                    cmd="ip addr flush dev %s"%item["name"]
                    print cmd
                    j.system.process.execute(cmd)


    def setBasicNetConfigurationDHCP(self,interface="eth0"):
        """
        this will bring all bridges down        
        """
        
        import pynetlinux
        import JumpScale.baselib.netconfig


        j.system.netconfig.reset(True)

        for br in pynetlinux.brctl.list_bridges():
            counter=0
            while br.is_up() and counter<10:
                br.down()
                time.sleep(1)
                counter+=1
                print "waiting for bridge:%s to go down"%br.name
        
        i=pynetlinux.ifconfig.findif(interface)
        if i<>None:            
            print "found %s, will try to bring down."%interface
            i.down()
            counter=0
            while i.is_up() and counter<10:
                i.down()
                time.sleep(1)
                counter+=1
                print "waiting for interface:%s to go down"%interface

            cmd="ip addr flush dev %s"%interface
            j.system.process.execute(cmd)

        
        j.system.netconfig.enableInterface(dev=interface,start=True)
        
        print "check interface up"
        while i.is_up()==False:
            i.up()
            time.sleep(1)
            print "waiting for interface:%s to go up"%interface 

        print "interface:%s up"%interface

        print "check can reach 8.8.8.8"
        if not j.system.net.pingMachine("8.8.8.8"):
            j.events.opserror_critical("Cannot get to public dns, network configuration did not succeed for %s (dhcp)"%(interface))
        print "8.8.8.8 reachable"
        print "network config done."

    def setBasicNetConfigurationBridgePub(self,interface=None,ipaddr=None,gw=None,mask=None):
        """
        will in a safe way configure bridge brpub
        if available and has ip addr to go to internet then nothing will happen
        otherwise system will try in a safe way set this ipaddr, this is a dangerous operation

        if ipaddr == None then will look for existing config on interface and use that one to configure the bridge
        """
        import pynetlinux
        import JumpScale.baselib.netconfig
        if ipaddr==None or mask==None or interface==None:
            print "get default network config for main interface"
            interface2,ipaddr2=self.getDefaultIPConfig()
            if interface==None:
                interface=str(interface2)
                print "interface found:%s"%interface
            if ipaddr==None:
                ipaddr=ipaddr2
                print "ipaddr found:%s"%ipaddr

        if interface=="brpub":
            gw=pynetlinux.route.get_default_gw()
            if not j.system.net.pingMachine(gw,pingtimeout=2):
                raise RuntimeError("cannot continue to execute on bridgeConfigResetPub, gw was not reachable.")
            #this means the default found interface is already brpub, so can leave here
            return

        i=pynetlinux.ifconfig.Interface(interface)

        try:
            i.mac
        except IOError, e:
            if e.errno == 19:
                raise RuntimeError("Did not find interface: %s"%interface)
            else:
                raise

        if ipaddr==None:
            raise RuntimeError("Did not find ipaddr: %s"%ipaddr)


        if mask==None:
            mask=i.get_netmask()
            print "mask found:%s"%mask

        if gw==None:
            gw=pynetlinux.route.get_default_gw()
            print "gw found:%s"%gw

        if gw==None:
            raise RuntimeError("Did not find gw: %s"%gw)            

        if not j.system.net.pingMachine(gw,pingtimeout=2):
            raise RuntimeError("cannot continue to execute on bridgeConfigResetPub, gw was not reachable.")
        print "gw can be reached"



        if self.bridgeExists("brpub"):
            br=pynetlinux.brctl.findbridge("brpub")
            br.down()
            cmd="brctl delbr brpub"
            j.system.process.execute(cmd)

        try:
            import netaddr
            n=netaddr.IPNetwork("%s/%s"%(ipaddr,mask))
            self.removeNetworkFromInterfaces(str(n.network.ipv4()))

            #bring all other brdiges down
            for br in pynetlinux.brctl.list_bridges():
                counter=0
                while br.is_up() and counter<10:
                    br.down()
                    time.sleep(1)
                    counter+=1
                    print "waiting for bridge:%s to go down"%br.name
            
            #bring own interface down
            i=pynetlinux.ifconfig.findif(interface)
            if i<>None:            
                print "found %s, will try to bring down."%interface
                i.down()
                counter=0
                while i.is_up() and counter<10:
                    i.down()
                    time.sleep(1)
                    counter+=1
                    print "waiting for interface:%s to go down"%interface

                cmd="ip addr flush dev %s"%interface
                j.system.process.execute(cmd)


            j.do.execute("sudo stop network-manager",outputStdout=False,outputStderr=False,dieOnNonZeroExitCode=False)
            j.do.writeFile("/etc/init/network-manager.override","manual")

            j.system.netconfig.reset()

            #now we should have no longer a network & all is clean
            j.system.netconfig.enableInterface(dev=interface,start=False,dhcp=False)
            j.system.netconfig.enableInterfaceBridgeStatic(dev="brpub",ipaddr="%s/%s"%(ipaddr,mask),bridgedev=interface,gw=gw,start=True)

            j.system.netconfig.setNameserver("8.8.8.8")

        except Exception,e:
            print "error in bridgeConfigResetPub:'%s'"%e            
            j.system.net.setBasicNetConfiguration(interface,ipaddr,gw,mask,config=False)


        return interface,ipaddr,mask,gw



    def getNetworkInfo(self):
        """
        returns {macaddr_name:[ipaddr,ipaddr],...}

        REMARK: format changed because there was bug which could not work with bridges

        @TODO change for windows

        """ 
        netaddr={}
        if j.system.platformtype.isLinux():
            return [item for item in getNetworkInfo()]
            # ERROR: THIS DOES NOT WORK FOR BRIDGED INTERFACES !!! because macaddr is same as host interface
            # for ipinfo in getNetworkInfo():
            #     print ipinfo
            #     ip = ','.join(ipinfo['ip'])
            #     netaddr[ipinfo['mac']] = [ ipinfo['name'], ip ]
        else:
            nics=self.getNics()
            for nic in nics:
                mac=self.getMacAddress(nic)
                ips=[item[0] for item in self.getIpAddress(nic)]
                if nic.lower()!="lo":
                    netaddr[mac]=[nic.lower(),",".join(ips)]
        return  netaddr

    def getIpAddress(self, interface):
        """Return a list of ip addresses and netmasks assigned to this interface"""
        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            command = "ip a s %s" % interface
            (exitcode, output) = j.system.process.execute(command, outputToStdout=False, dieOnNonZeroExitCode=False)
            if exitcode != 0:
                return []
            nicinfo = re.findall("^\s+inet\s+(.*)\/(\d+)\s(?:brd\s)?(\d+\.\d+\.\d+\.\d+)?\s?scope.*$",output,re.MULTILINE)
            result = []
            for ipinfo in nicinfo:
                ip = ipinfo[0]
                masknumber = int(ipinfo[1])
                broadcast = ipinfo[2]
                mask = ""
                for i in range(4):
                    mask += str(int(hex(pow(2,32)-pow(2,32-masknumber))[2:][i*2:i*2+2],16)) + "."
                result.append([ip, mask[:-1], broadcast])
            return result
        elif j.system.platformtype.isSolaris():
            command = "ifconfig %s"%(interface)
            (exitcode, output) = j.system.process.execute(command, outputToStdout=False, dieOnNonZeroExitCode=False)
            if exitcode != 0:
                return []
            result = []
            match = re.search("^\s+inet\s+(?P<ipaddress>[\d\.]+)\s+.*netmask\s+(?P<netmask>[a-f\d]{8})\s?(broadcast)?\s?(?P<broadcast>[\d\.]+)?$", output, re.MULTILINE)
            if not match:
                return []
            ip = match.group('ipaddress')
            netmaskhex = match.group('netmask')
            broadcast = match.group('broadcast')
            mask =""
            for i in range(4):
                mask += str(int(netmaskhex[i*2:i*2+2], 16)) + "."
            return [[ip , mask[:-1], broadcast]]
        elif j.system.platformtype.isWindows():
            import wmi
            ipv4Pattern = '^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
            
            w = wmi.WMI()
            NICIndex = interface.split(":")[0]
            nic = w.Win32_NetworkAdapterConfiguration(index=NICIndex)[0]
            result = []
            if nic.IPAddress:
                for x in range(0, len(nic.IPAddress)):
                    # skip IPv6 addresses for now
                    if re.match(ipv4Pattern, str(nic.IPAddress[x])) != None: 
                        result.append( [str(nic.IPAddress[x]), str(nic.IPSubnet[x]), ''] )
            return result
        else:
            raise RuntimeError("j.system.net.getIpAddress not supported on this platform")

    def getMacAddress(self, interface):
        """Return the MAC address of this interface"""
        if not interface in self.getNics():
            raise LookupError("Interface %s not found on the system" % interface)
        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            if j.system.fs.exists("/sys/class/net"):
                return j.system.fs.fileGetContents('/sys/class/net/%s/address' % interface).strip()
            else:
                command = "ifconfig %s | grep HWaddr| awk '{print $5}'"% interface
                (exitcode,output)=j.system.process.execute(command, outputToStdout=False)
                return self.pm_formatMacAddress(output)
        elif j.system.platformtype.isSolaris():
            # check if interface is a logical inteface ex: bge0:1
            tokens = interface.split(':')
            if len(tokens) > 1 :
                interface = tokens[0]
            command = "ifconfig %s" % interface
            (exitcode, output) = j.system.process.execute(command, outputToStdout=False, dieOnNonZeroExitCode=False)
            if exitcode != 0:
                # temporary plumb the interface to lookup its mac
                j.logger.log("Interface %s is down. Temporarily plumbing it to be able to lookup its MAC address" % interface, 1)
                j.system.process.execute('%s plumb' % command, outputToStdout=False)
                (exitcode, output) = j.system.process.execute(command, outputToStdout=False, dieOnNonZeroExitCode=False)
                j.system.process.execute('%s unplumb' % command, outputToStdout=False)
            if exitcode == 0:
                match = re.search(r"^\s*(ipib|ether)\s*(?P<mac>\S*)", output, re.MULTILINE)
                if match:
                    return self.pm_formatMacAddress(match.group("mac"))
            return None
        elif j.system.platformtype.isWindows():
            import wmi
            w = wmi.WMI()   
            NICIndex = interface.split(":")[0]
            return str(w.Win32_NetworkAdapterConfiguration(index=NICIndex)[0].MACAddress)
        else:
            raise RuntimeError("j.system.net.getMacAddress not supported on this platform")

    def pm_formatMacAddress(self, macaddress):
        macpieces = macaddress.strip().split(':')
        mac = ""
        for piece in macpieces:
            if len(piece)==1:
                mac += "0"
            mac += piece + ":"
        mac = mac[:-1]
        return mac

    def isIpLocal(self, ipaddress):
        if ipaddress=="127.0.0.1" or ipaddress=="localhost":
            return True
        return ipaddress in self.getIpAddresses()

    def getMacAddressForIp(self, ipaddress):
        """Search the MAC address of the given IP address in the ARP table

        @param ipaddress: IP address of the machine
        @rtype: string
        @return: The MAC address corresponding with the given IP
        @raise: RuntimeError if no MAC found for IP or if platform is not suppported
        """
        def doArp(ipaddress):
            args = list()
            if j.system.platformtype.isLinux():
                # We do not want hostnames to show up in the ARP output
                args.append("-n")

            return j.system.process.execute(
                'arp %s %s' % (" ".join(args), ipaddress),
                dieOnNonZeroExitCode=False,
                outputToStdout=False
            )

        def noEntry(output):
            return ("no entry" in output) or ("(incomplete)" in output)

        if j.system.platformtype.isUnix():
            if self.isIpInDifferentNetwork(ipaddress):
                warning = 'The IP address %s is from a different subnet. This means that the macaddress will be the one of the gateway/router instead of the correct one.'
                j.errorconditionhandler.raiseWarning(warning % ipaddress)

            exitcode, output = doArp(ipaddress)
            # Output of arp is 1 when no entry found is 1 on solaris but 0
            # on Linux, so we check the actual output
            if noEntry(output):
                # ping first and try again
                self.pingMachine(ipaddress, pingtimeout=1)
                exitcode, output = doArp(ipaddress)

            if not noEntry(output) and j.system.platformtype.isSolaris():
                mac = output.split()[3]
                return self.pm_formatMacAddress(mac)
            else:
                mo = re.search("(?P<ip>[0-9]+(.[0-9]+){3})\s+(?P<type>[a-z]+)\s+(?P<mac>([a-fA-F0-9]{2}[:|\-]?){6})",output)
                if mo:
                    return self.pm_formatMacAddress(mo.groupdict()['mac'])
                else:
                    # On Linux the arp will not show local configured ip's in the table.
                    # That's why we try to find the ip with "ip a" and match for the mac there.

                    output, stdout, stderr = j.system.process.run('ip a', stopOnError=False)
                    if exitcode:
                        raise RuntimeError('Could not get the MAC address for [%s] because "ip" is not found'%s)
                    mo = re.search('\d:\s+\w+:\s+.*\n\s+.+\s+(?P<mac>([a-fA-F0-9]{2}[:|\-]?){6}).+\n\s+inet\s%s[^0-9]+'%ipaddress, stdout, re.MULTILINE)
                    if mo:
                        return self.pm_formatMacAddress(mo.groupdict()['mac'])
            raise RuntimeError("MAC address for [%s] not found"%ipaddress)
        else:
            raise RuntimeError("j.system.net.getMacAddressForIp not supported on this platform")

    def getHostname(self):
        """Get hostname of the machine
        """
        return socket.gethostname()

    def isNicConnected(self,interface):
        if j.system.platformtype.isLinux():
            carrierfile = '/sys/class/net/%s/carrier'%(interface)
            if not j.system.fs.exists(carrierfile):
                return False
            try:
                return int(j.system.fs.fileGetContents(carrierfile)) != 0
            except IOError:
                return False
        elif j.system.platformtype.isESX():
            nl = j.system.net.getNics(up=True)
            if interface not in nl:
                return False
            else:
                return True
        elif j.system.platformtype.isSolaris():
            if j.system.platformtype.getVersion() < 100:
                command = "dladm show-dev -p -o STATE %s" % interface
                expectResults = ['STATE="up"', 'STATE="unknown"']
            else:
                command = "dladm show-phys -p -o STATE %s" % interface
                expectResults = ['up', 'unknown']

            (exitcode, output) = j.system.process.execute(command, dieOnNonZeroExitCode=False, outputToStdout=False)
            if exitcode != 0:
                return False
            output = output.strip()
            if output in expectResults:
                return True
            else:
                return False

    def getHostByName(self, dnsHostname):
        import socket
        return socket.gethostbyname(dnsHostname)
    def getDefaultRouter(self):
        """Get default router
        @rtype: string representing the router interface
        """
        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            command = "ip r | grep 'default' | awk {'print $3'}"
            (exitcode, output) = j.system.process.execute(command, outputToStdout=False)
            return output.strip()
        elif j.system.platformtype.isSolaris():
            command = "netstat -rn | grep default | awk '{print $2}'"
            (exitcode, output) = j.system.process.execute(command, outputToStdout=False)
            return output.strip()
        else:
            raise RuntimeError("j.system.net.getDefaultRouter not supported on this platform")

    def validateIpAddress(self, ipaddress):
        """Validate wether this ip address is a valid ip address of 4 octets ranging from 0 to 255 or not
        @param ipaddress: ip address to check on
        @rtype: boolean...True if this ip is valid, False if not
        """
        if len(ipaddress.split()) == 1:
            ipList = ipaddress.split('.')
            if len(ipList) == 4:
                for i, item in enumerate(ipList):
                    try:
                        ipList[i] = int(item)
                    except:
                        return False
                    if not isinstance(ipList[i], int):
                        j.logger.log('[%s] is not a valid ip address, octects should be integers'%ipaddress, 7)
                        return False
                if max(ipList) < 256:
                    j.logger.log('[%s] is a valid ip address'%ipaddress, 9)
                    return True
                else:
                    j.logger.log('[%s] is not a valid ip address, octetcs should be less than 256'%ipaddress, 7)
                    return False
            else:
                j.logger.log('[%s] is not a valid ip address, ip should contain 4 octets'%ipaddress, 7)
                return False
        else:
            j.logger.log('[%s] is not a valid ip address'%ipaddress, 7)
            return False

    def pingMachine(self, ip, pingtimeout=60, recheck = False, allowhostname = True):
        """Ping a machine to check if it's up/running and accessible
        @param ip: Machine Ip Address
        @param pingtimeout: time in sec after which ip will be declared as unreachable
        @param recheck: Unused, kept for backwards compatibility
        @param allowhostname: allow pinging on hostname (default is false)
        @rtype: True if machine is pingable, False otherwise
        """
        if not allowhostname:
            if not j.system.net.validateIpAddress(ip):
                raise ValueError('ERROR: invalid ip address passed:[%s]'%ip)

        j.logger.log('pingMachine %s, timeout=%d, recheck=%s' % (ip, pingtimeout, str(recheck)), 8)

        start = time.time()
        pingsucceeded = False
        while time.time() - start < pingtimeout:
            # if j.system.platformtype.isSolaris():
            #     #ping -c 1 IP 1
            #     #Last 1 is timeout in seconds
            #     exitcode, output = j.system.process.execute(
            #                         'ping -c 1 %s 1' % ip, False, False)
            if j.system.platformtype.isLinux():
                #ping -c 1 -W 1 IP
                exitcode, output = j.system.process.execute(
                                    'ping -c 1 -W 1 -w 1 %s' % ip, False, False)
            elif j.system.platformtype.isUnix():
                exitcode, output = j.system.process.execute('ping -c 1 %s'%ip, False, False)
            elif j.system.platformtype.isWindows():
                exitcode, output = j.system.process.execute('ping -w %d %s'%(pingtimeout, ip), False, False)
            else:
                raise RuntimeError('Platform is not supported')
            if exitcode == 0:
                pingsucceeded = True
                j.logger.log('Machine with ip:[%s] is pingable'%ip, 9)
                return True
            time.sleep(1)
        if not pingsucceeded:
            j.logger.log("Could not ping machine with ip:[%s]"%ip, 7)
            return False


    def isIpInHostsFile(self, hostsfile, ip):
        """Check if ip is in the hostsfile
        @param hostsfile: File where hosts are defined
        @param ip: Ip of the machine to check
        """
        # get content of hostsfile
        filecontents = j.system.fs.fileGetContents(hostsfile)
        res = re.search('^%s\s' %ip, filecontents, re.MULTILINE)
        if res:
            return True
        else:
            return False

    def removeFromHostsFile(self, hostsfile, ip):
        """Update a hostfile, delete ip from hostsfile
        @param hostsfile: File where hosts are defined
        @param ip: Ip of the machine to remove
        """
        j.logger.log('Updating hosts file %s: Removing %s' % (hostsfile, ip), 8)
        # get content of hostsfile
        filecontents = j.system.fs.fileGetContents(hostsfile)
        searchObj = re.search('^%s\s.*\n' %ip, filecontents, re.MULTILINE)
        if searchObj:
            filecontents = filecontents.replace(searchObj.group(0), '')
            j.system.fs.writeFile(hostsfile, filecontents)
        else:
            j.logger.log('Ip address %s not found in hosts file' %ip, 1)
            
    def getHostNamesForIP(self, hostsfile, ip):
        """Get hostnames for ip address
        @param hostsfile: File where hosts are defined
        @param ip: Ip of the machine to get hostnames from
        @return: List of machinehostnames
        """
        j.logger.log('Get hostnames from hosts file %s for ip %s' % (hostsfile, ip), 8)
        # get content of hostsfile
        if self.isIpInHostsFile(hostsfile, ip):
            filecontents = j.system.fs.fileGetContents(hostsfile)
            searchObj = re.search('^%s\s.*\n' %ip, filecontents, re.MULTILINE)
            hostnames = searchObj.group(0).strip().split()
            hostnames.pop(0)
            return hostnames
        else:
            return []

    def updateHostsFile(self,hostsfile,ip,hostname):
        """Update a hostfile to contain the basic information install
        @param hostsfile: File where hosts are defined
        @param ip: Ip of the machine to add/modify
        @param hostname: List of machinehostnames to add/modify
        """
        if isinstance(hostname, str):
            hostname = hostname.split()
        j.logger.log('Updating hosts file %s: %s -> %s' % (hostsfile, hostname, ip), 8)
        # get content of hostsfile
        filecontents = j.system.fs.fileGetContents(hostsfile)
        searchObj = re.search('^%s\s.*\n' %ip, filecontents, re.MULTILINE)
        
        hostnames = ' '.join(hostname)
        if searchObj:
            filecontents = filecontents.replace(searchObj.group(0), '%s %s\n' %(ip, hostnames))
        else:
            filecontents += '%s %s\n' %(ip, hostnames)

        j.system.fs.writeFile(hostsfile, filecontents)


    def download(self, url, localpath, username=None, passwd=None):
        '''Download a url to a file or a directory, supported protocols: http, https, ftp, file
        @param url: URL to download from
        @type url: string
        @param localpath: filename or directory to download the url to pass - to return data
        @type localpath: string
        @param username: username for the url if it requires authentication
        @type username: string
        @param passwd: password for the url if it requires authentication
        @type passwd: string
        '''
        if not url:
            raise ValueError('URL can not be None or empty string')
        if not localpath:
            raise ValueError('Local path to download the url to can not be None or empty string')
        filename = ''
        if localpath == '-':
            filename = '-'
        if j.system.fs.isDir(localpath):
            filename = j.system.fs.joinPaths(localpath, j.system.fs.getBaseName(url))
        else:
            if j.system.fs.isDir(j.system.fs.getDirName(localpath)) and not j.system.fs.exists(localpath):
                filename = localpath
            else:
                raise ValueError('Local path is an invalid path')
        j.logger.log('Downloading url %s to local path %s'%(url, filename), 4)
        from urllib import FancyURLopener
        from urllib import splittype
        class myURLOpener(FancyURLopener):
            # read a URL, with automatic HTTP authentication
            def __init__(self, user, passwd):
                self._user = user
                self._passwd = passwd
                self._promptcalled = False
                FancyURLopener.__init__(self)

            def prompt_user_passwd(self, host, realm):
                if not self._user or not self._passwd:
                    raise RuntimeError('Server requested authentication but nothing was given')
                if not self._promptcalled:
                    self._promptcalled = True
                    return self._user, self._passwd
                raise RuntimeError('Could not authenticate with the given authentication user:%s and password:%s'%(self._user, self._passwd))

        urlopener = myURLOpener(username, passwd)
        if username and passwd and splittype(url)[0] == 'ftp':
            url = url.split('://')[0]+'://%s:%s@'%(username,passwd)+url.split('://')[1]
        if filename != '-':
            urlopener.retrieve(url, filename, None, None)
            j.logger.log('URL %s is downloaded to local path %s'%(url, filename), 4)
        else:
            return urlopener.open(url).read()

    def getDomainName(self):
        """
        Retrieve the dns domain name
        """
        cmd = "dnsdomainname" if j.system.platformtype.isLinux() else "domainname" if j.system.platformtype.isSolaris() else ""
        if not cmd:
            raise PlatformNotSupportedError('Platform "%s" is not supported. Command is only supported on Linux and Solaris' % j.system.platformtype.name)

        exitCode, domainName = j.system.process.execute(cmd, outputToStdout=False)

        if not domainName:
            raise ValueError('Failed to retrieve domain name')

        domainName = domainName.splitlines()[0]

        return domainName

class PlatformNotSupportedError(RuntimeError): pass

class NetworkZone:
    ipRanges=None ##array(IPRange)
