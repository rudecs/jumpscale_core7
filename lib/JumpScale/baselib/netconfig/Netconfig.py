from JumpScale import j
import netaddr
try:
    import JumpScale.lib.ovsnetconfig
except Exception as e:
    pass

import JumpScale.baselib.codetools

class Netconfig:
    """
    """

    def __init__(self):
        self.root="/"

    def setRoot(self,root):
        self.root=root
        if not j.system.fs.exists(path=root):
            raise RuntimeError("Cannot find root for netconfig:%s"%root)
        #set base files
        for item in ["etc/network/interfaces","etc/resolv.conf"]:
            j.system.fs.touch(j.system.fs.joinPaths(self.root,item),overwrite=False)

    def shutdownNetwork(self,excludes=[]):
        """
        find all interfaces and shut them all down with ifdown
        this is to remove all networking things going on
        """
        excludes.append("lo")
        for nic in j.system.net.getNics():
            if nic not in excludes:
                cmd="ifdown %s --force"%nic
                print(("shutdown:%s"%nic))
                j.system.process.execute(cmd,dieOnNonZeroExitCode=False)
        
    def _getInterfacePath(self):
        path=j.system.fs.joinPaths(self.root,"etc/network/interfaces")
        if not j.system.fs.exists(path):
            raise RuntimeError("Could not find network interface path: %s"%path)
        return path

    def _backup(self,path):
        backuppath=path+".backup"
        counter=1
        while j.system.fs.exists(path=backuppath):
            counter+=1
            backuppath=path+".backup.%s"%counter
        j.system.fs.copyFile(path,backuppath)

    def reset(self,shutdown=False):
        """
        empty config of /etc/network/interfaces
        """
        if shutdown:
            self.shutdownNetwork()
        path=self._getInterfacePath()
        self._backup(path)
        j.system.fs.writeFile(path,"auto lo\n\n")
        

    def enableInterface(self,dev="eth0",start=False,dhcp=True):

        if dhcp:

            C="""
auto $int
iface eth0 inet dhcp
"""
        else:
            C="""
auto $int
iface eth0 inet manual
"""

        C=C.replace("$int",dev)
        path=self._getInterfacePath()
        ed=j.codetools.getTextFileEditor(path)
        ed.setSection(dev,C)
        if start:
            cmd="ifdown %s"%dev
            print(("down:%s"%dev))
            j.system.process.execute(cmd)     
            cmd="ifup %s"%dev
            print(("up:%s"%dev))
            j.system.process.execute(cmd)     
        if dhcp:
            print "refresh dhcp"
            j.system.process.execute("dhclient %s"%dev)  


    def remove(self,dev):
        path=self._getInterfacePath()
        ed=j.codetools.getTextFileEditor(path)
        ed.removeSection(dev)



    def setNameserver(self,addr):
        """
        resolvconf will be disabled
        
        """
        cmd="resolvconf --disable-updates"
        j.system.process.execute(cmd)
        C="nameserver %s\n"%addr    
        path=j.system.fs.joinPaths(self.root,"etc/resolv.conf")
        if not j.system.fs.exists(path):
            pass  #@todo???? does not work         
            # raise RuntimeError("Could not find resolv.conf path: '%s'"%path)
        j.system.fs.writeFile(path,C)


    def enableInterfaceStatic(self,dev,ipaddr,gw=None,start=False):
        """
        ipaddr in form of 192.168.10.2/24 (can be list)
        gateway in form of 192.168.10.254
        """
        C="""
auto $int        
iface $int inet static
       address $ip
       netmask $mask
       network $net
"""
        if gw!=None:
            C+="       gateway %s"%gw

        args={}
        args["dev"]=dev
        args["ipaddr"]=ipaddr
        self._applyNetconfig(dev,C,args,start=start)

    def enableInterfaceBridgeStatic(self,dev,ipaddr=None,bridgedev=None,gw=None,start=False):
        """
        ipaddr in form of 192.168.10.2/24 (can be list)
        gateway in form of 192.168.10.254
        """
        C="""
auto $int        
iface $int inet static
       bridge_fd 0
       bridge_maxwait 0
"""
        if ipaddr!=None:
            C+="""
       address $ip
       netmask $mask
       network $net            
"""
        else:
            C=C.replace("static","manual")
            
        if bridgedev!=None:
            C+="       bridge_ports $bridgedev\n"
        else:
            C+="       bridge_ports none\n"

        if gw!=None:
            C+="       gateway %s"%gw

#         future="""
#        #broadcast <broadcast IP here, e.g. 192.168.1.255>
#        # dns-* options are implemented by the resolvconf package, if installed
#        #dns-nameservers <name server IP address here, e.g. 192.168.1.1>
#        #dns-search your.search.domain.here

# """
        args={}
        args["dev"]=dev
        args["ipaddr"]=ipaddr
        if bridgedev!=None:
            args["bridgedev"]=bridgedev        
        self._applyNetconfig(dev,C,args,start=start)        

    def enableInterfaceBridgeDhcp(self,dev,bridgedev,start=False):
        self.enableInterfaceBridge(dev,bridgedev,start, True)

    def enableInterfaceBridge(self,dev,bridgedev,start=False,dhcp=True):
        """
        """
        C="""
auto $int        
iface $int inet $method
       bridge_ports $bridgedev
       bridge_fd 0
       bridge_maxwait 0
"""

        args={}
        args['method'] = 'dhcp' if dhcp else 'manual'
        args["dev"]=dev
        args["bridgedev"]=bridgedev        
        self._applyNetconfig(dev,C,args,start=start)        

    def addIpToInterface(self,dev,ipaddr,aliasnr=1,start=False):

        C="""
auto $int:$aliasnr        
iface $int:$aliasnr inet static
       name $int Alias
       address $ip
       netmask $mask
       network $net
""" 
        C=C.replace("$aliasnr",str(aliasnr))
        C=C.replace("$int",dev)

        args={}
        args["dev"]=dev
        args["ipaddr"]=ipaddr        
        self._applyNetconfig(dev+":%s"%aliasnr,C,args,start=start)  

    def _applyNetconfig(self,devToApplyTo,template,args,start=False):

        C=template
        dev=args["dev"]
        if "ipaddr" in args:
            ipaddr=args["ipaddr"]
            if ipaddr!=None:
                ip = netaddr.IPNetwork(ipaddr)
                C=C.replace("$ip",str(ip.ip))
                C=C.replace("$mask",str(ip.netmask))
                C=C.replace("$net",str(ip.network))

        C=C.replace("$int",dev)
        if 'method' in args:
            C = C.replace("$method", args['method'])
        
        if "gw" in args:
            C=C.replace("$gw","gateway %s"%args["gw"])
        if "bridgedev" in args:
            C=C.replace("$bridgedev",args["bridgedev"])
        path=self._getInterfacePath()
        ed=j.codetools.getTextFileEditor(path)
        ed.setSection(devToApplyTo,C)

        if start:
            print(("restart:%s"%devToApplyTo))
            cmd="ifdown %s"%devToApplyTo
            j.system.process.execute(cmd) 
            cmd="ifup %s"%devToApplyTo
            j.system.process.execute(cmd)

            if not devToApplyTo.startswith(dev):
                print(("restart:%s"%dev))
                cmd="ifdown %s"%dev
                j.system.process.execute(cmd) 
                cmd="ifup %s"%dev
                j.system.process.execute(cmd)
                
