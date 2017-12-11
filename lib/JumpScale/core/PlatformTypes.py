from JumpScale import j
import sys, os, re

def _useELFtrick(file):
    fd=os.open(file, os.O_RDONLY)
    out = os.read(fd,5)
    if out[0:4]!="\x7fELF":
        result = 0 # ELF trick fails...
    elif out[4] == '\x01':
        result = 32
    elif out[4] == '\x02':
        result = 64
    else:
        result = 0
    os.close(fd)
    return result


class PlatformTypes():

    def __init__(self):
        self.myplatform=self._getPlatform()        
        self.platformParents={}
        self.addPlatform("unknown",parent="")
        self.addPlatform("generic",parent="unknown")
        self.addPlatform("unix",parent="generic")
        self.addPlatform("linux",parent="unix")
        self.addPlatform("linux32",parent="linux")
        self.addPlatform("linux64",parent="linux")
        self.addPlatform("ubuntu",parent="linux")
        self.addPlatform("ubuntu32",parent="ubuntu")
        self.addPlatform("ubuntu32",parent="linux32")
        self.addPlatform("ubuntu64",parent="ubuntu")
        self.addPlatform("ubuntu64",parent="linux64")
        self.addPlatform("mint",parent="ubuntu")
        self.addPlatform("mint32",parent="mint")
        self.addPlatform("mint64",parent="mint")
        self.addPlatform("mint32",parent="ubuntu32")
        self.addPlatform("mint64",parent="ubuntu64")
        self.addPlatform("cygwin",parent="linux32")
        self.addPlatform("win",parent="generic")
        self.addPlatform("win32",parent="win")
        self.addPlatform("win64",parent="win")
        self.addPlatform("win7",parent="win")
        self.addPlatform("win8",parent="win")
        self.addPlatform("vista",parent="win")
        self.addPlatform("darwin",parent="unix")
        self.addPlatform("win2008_64",parent="win64")
        self.addPlatform("win2012_64",parent="win64")
        

    def getMyRelevantPlatforms(self):
        return self.platformParents[str(self.myplatform).lower()]

    def checkMatch(self,match):
        """
        match is in form of linux64,darwin
        if any of the items e.g. darwin is in getMyRelevantPlatforms then return True
        """
        tocheck=self.getMyRelevantPlatforms()
        matches = [item.strip().lower() for item in match.split(",") if item.strip()!=""]
        for match in matches:
            if match in tocheck:
                return True
        return False


    def getPlatforms(self):
        return list(self.platformParents.keys())

    def getParents(self,name):            
        result=self.platformParents[name]
        try:
            result.pop(result.index(""))
        except:
            pass
        return result

    def getChildren(self,name):
        raise NotImplemented("getchildren not implemented")

    def addPlatform(self,name,parent):
        # print "TRY addparent: %s %s"%(name,parent)
        name=name.lower()
        parent=parent.lower()
        if name not in self.platformParents:
            self.platformParents[name]=[name]
        if not parent or name == parent:
            return
        if parent not in self.platformParents[name]:
            self.platformParents[name].append(parent)
        if parent in self.platformParents:
            for parentofparent in self.platformParents[parent]:
                if parentofparent != parent:
                    self.addPlatform(name,parentofparent)
        else:
            if parent!="":
                raise RuntimeError("Could not find parent %s in tree, probably order of insertion not ok."%parent)

    def isVirtual(self):
        return self.getVirtual() != 'none'

    def getVirtual(self):
        _, type_ = j.system.process.execute('systemd-detect-virt', dieOnNonZeroExitCode=False)
        return type_.strip()


    def _getPlatform(self):

        '''Discovers the platform'''
        _platform = None

        if sys.platform.startswith("linux"):

            import lsb_release
            info = lsb_release.get_distro_information()['ID'].lower()

            bits = _useELFtrick("/sbin/init")
            
            if bits == 32:
                if info == 'ubuntu':
                    _platform = "ubuntu32"
                elif info == 'linuxmint':
                    _platform = "mint32"
                else:
                    _platform = "linux32"
            elif bits == 64 or bits==0:  #@todo does not work in python 3 anymore
                if info == 'ubuntu':
                    _platform = "ubuntu64"
                elif info == 'linuxmint':
                    _platform = "mint64"
                else:
                    _platform = "linux64"
            else:
                raise RuntimeError("dont find which nr bits in platform")
            
            # if os.path.exists("/proc/vmware"):
            #     _platform = PlatformType.ESX

        # elif sys.platform.startswith("sunos"):
        #     import commands
        #     _, bits = commands.getstatusoutput('isainfo -b')
        #     bits = int(bits)
        #     if bits == 32:
        #         _platform = PlatformType.SOLARIS32
        #     elif bits == 64:
        #         _platform = PlatformType.SOLARIS64
        #     else:
        #         _platform = PlatformType.UNKNOWN

        elif sys.platform.startswith("win"):
            _platform = "win64"

        elif sys.platform.startswith("cygwin"):
            _platform = "cygwin"

        elif sys.platform.startswith("darwin"):
            _platform = "darwin"

        else:
            raise RuntimeError("can't establish platform name")



        return _platform        

    def has_parent(self,name):
        if name==self.myplatform:
            return True
        return name in self.platformParents[self.myplatform]

    def dieIfNotPlatform(self,platform):
        if not self.has_parent(platform):
            raise RuntimeError("Can not continue, supported platform is %s, this platform is %s"%(platform,self.myplatform))

    def isUnix(self):
        '''Checks whether the platform is Unix-based'''
        return self.has_parent("unix")

    def isWindows(self):
        '''Checks whether the platform is Windows-based'''
        return self.has_parent("win")

    def isLinux(self):
        '''Checks whether the platform is Linux-based'''
        return self.has_parent("linux")

    def isGeneric(self):
        '''Checks whether the platform is generic (they all should)'''
        return self.has_parent("generic")
    
    def isXen(self):
        '''Checks whether Xen support is enabled'''
        return j.system.process.checkProcess('xen') == 0
    
    def isVirtualBox(self):
        '''Check whether the system supports VirtualBox'''
        if self.isWindows():
            #@TODO P3 Implement proper check if VBox on Windows is supported
            return False
        exitcode, stdout, stderr = j.system.process.run('lsmod |grep vboxdrv |grep -v grep', stopOnError=False)
        return exitcode == 0
    
    def isHyperV(self):
        '''Check whether the system supports HyperV'''
        if self.isWindows():
            import winreg as wr
            try:
                virt = wr.OpenKey(wr.HKEY_LOCAL_MACHINE, 'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Virtualization', 0, wr.KEY_READ | wr.KEY_WOW64_64KEY)
                wr.QueryValueEx(virt, 'Version')
            except WindowsError:
                return False
            return True
        return False
    
    def __str__(self):
        return str(self.platformParents)

    __repr__=__str__

        

        
