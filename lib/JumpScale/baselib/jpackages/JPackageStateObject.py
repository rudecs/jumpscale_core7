from JumpScale import j

class JPackageStateObject():
    
    def __init__(self,jpackagesObject):
        key="%s_%s_%s" % (jpackagesObject.domain,jpackagesObject.name,jpackagesObject.version)
        self._path = j.system.fs.joinPaths(j.dirs.cfgDir, "jpackages", "state", key + ".cfg")

        if not j.system.fs.exists(self._path):
            self._ini=j.tools.inifile.new(self._path)
            self._ini.addSection("main")
            self.lastinstalledbuildnr=-1
            self.lastdownloadedbuildnr=-1
            self.lastexpandedbuildnr=-1
            self.lastaction=""
            self.lasttag=""
            self.lastactiontime=0
            self.currentaction=""
            self.currenttag=""
            self.currentactiontime=0
            #self.state="OK"
            self.retry=0 #nr of times we tried to repair last broken state
            self.prepared=0
            self.isPendingReconfiguration=0
            self.debugMode = 0
            self.downloadedBlobStorKeys={}  #is dict with key platform & value the key
            self.installedBlobStorKeys={}#is dict with key platform & value the key
            self._save()
        else:
            self._ini=j.tools.inifile.open(self._path)
            self.lastinstalledbuildnr=int(self._ini.getValue("main","lastinstalledbuildnr"))
            self.lastexpandedbuildnr=int(self._ini.getValue("main","lastexpandedbuildnr"))
            self.lastdownloadedbuildnr=int(self._ini.getValue("main","lastdownloadedbuildnr"))
            self.lastaction=self._ini.getValue("main","lastaction")
            self.lasttag=self._ini.getValue("main","lasttag")
            self.lastactiontime=int(self._ini.getValue("main","lastactiontime"))
            self.currentaction=self._ini.getValue("main","currentaction")
            self.currenttag=self._ini.getValue("main","currenttag")
            self.currentactiontime=self._ini.getValue("main","currentactiontime")
            self.downloadedBlobStorKeys=self._strToDict(self._ini.getValue("main","downloadedblobstorkeys"))
            self.installedBlobStorKeys=self._strToDict(self._ini.getValue("main","installedblobstorkeys"))

            #print 'Asking enum : ' + self._ini.getValue("main","state") + ' from ' + str(self._ini)
            #self.state=j.enumerators.JPackageState4.getByName(self._ini.getValue("main","state"))
            self.retry=int(self._ini.getValue("main","retry"))
            self.prepared=int(self._ini.getValue("main","prepared"))
            if self._ini.checkParam("main", "debugMode"):
                self.debugMode = int(self._ini.getValue("main", "debugMode"))
            else:
                self.debugMode = 0

            self.isPendingReconfiguration=int(self._ini.getValue("main","isPendingReconfiguration"))
             
    def _strToDict(self,s):
        d={}
        for item in s.split(","):
            if item.strip() != "":
                platform,key=item.split(":")
                d[platform]=key
        return d

    def _dictToStr(self,d):
        s=""
        for platform in list(d.keys()):
            key=d[platform]
            s+="%s:%s,"%(platform,key)
        s=s[:-1]
        return s
            
    def _save(self):
        self._ini.setParam("main","lastinstalledbuildnr",self.lastinstalledbuildnr)
        self._ini.setParam("main","lastexpandedbuildnr",self.lastexpandedbuildnr)
        self._ini.setParam("main","lastdownloadedbuildnr",self.lastdownloadedbuildnr)
        self._ini.setParam("main","lastaction",self.lastaction)
        self._ini.setParam("main","lasttag",self.lasttag)
        self._ini.setParam("main","lastactiontime",self.lastactiontime)
        self._ini.setParam("main","currentaction",self.currentaction)
        self._ini.setParam("main","currenttag",self.currenttag)
        self._ini.setParam("main","currentactiontime",self.currentactiontime)
        #print "in JPackageStateObject save: " + str(self.state)
        #self._ini.setParam("main","state",self.state)
        self._ini.setParam("main","retry",self.retry)
        self._ini.setParam("main","prepared",self.prepared)
        self._ini.setParam("main","isPendingReconfiguration",self.isPendingReconfiguration)
        self._ini.setParam("main","debugMode",self.debugMode)    
        self._ini.setParam("main","downloadedblobstorkeys",self._dictToStr(self.downloadedBlobStorKeys))
        self._ini.setParam("main","installedblobstorkeys",self._dictToStr(self.installedBlobStorKeys))
        self._ini.write()
        
    def save(self):
        self._save()
    def setDebugMode(self, mode=1):
        '''
        enables debug mode for jpackages
        '''
        self.debugMode = mode
        self._save()
        
    def getDebugMode(self):
        return self.debugMode
    
    def setLastInstalledBuildNr(self, buildNr):
        """
        Sets the last buildnumber to the one given as parameter
        """
        self.lastinstalledbuildnr = buildNr
        self._save()
        
    def setLastExpandedBuildNr(self, buildNr):
        """
        Sets the last expanded build number to the one given as parameter
        """
        self.lastexpandedbuildnr = buildNr
        self._save()
        
    def setLastDownloadedBuildNr(self, buildNr):
        """
        Sets the last downloaded build number to the one given as parameter
        """
        self.lastdownloadedbuildnr = buildNr
        self._save()
        
    def setIsPendingReconfiguration(self, value):
        """
        Changes the jpackages's config file to see whether reconfiguration is required or not depending on the value given as parameter
        """
        value = str(value).lower()
        if value == '1' or value == 'true':
            value=1
        else:
            value=0
        self.isPendingReconfiguration = value
        self.save()

    def getIsPendingReconfiguration(self):
        """
        Returns true is the jpackages needs reconfiguration
        """
        return self.isPendingReconfiguration

    def setCurrentAction(self,tag,action):
        """
        @param tag  e.g. install
        @param action e.g. checkout when tag=codemgmt
        """        
        if self.currenttag != "":
            self.lasttag=self.currenttag
        if self.currentaction != "":
            self.lastaction=self.currentaction
        if self.currentactiontime != 0:
            self.lastactiontime=self.currentactiontime
        self.currentactiontime=j.base.time.getTimeEpoch()
        self.currentaction=action
        self.currenttag=tag
        self._save()
        
    def setCurrentActionIsDone(self):
        """
        current action is succesfully completed
        """
        self.setCurrentAction("","")
        self.state="OK"
        self._save()

    def setPrepared(self, prepared):
        """
        Changes the jpackages config file to whether the package has been prepared or not depending on the parameter given
        """
        self.prepared=prepared
        self._save()
        
    def checkNoCurrentAction(self):
        """
        if no current action return True
        """
        if self.state=="OK" and self.currentaction=="":
            return True
        return False
    
    def __str__(self):
        string  = "lastinstalledbuildnr:"  + str(self.lastinstalledbuildnr)  + '\n'
        string += "lastdownloadedbuildnr:" + str(self.lastdownloadedbuildnr) + '\n'
        string += "lastexpandedbuildnr:"   + str(self.lastexpandedbuildnr)   + '\n'
        string += "lastaction:"            + str(self.lastaction)            + '\n'
        string += "lasttag:"               + str(self.lasttag)               + '\n'
        string += "lastactiontime:"        + str(self.lastactiontime)        + '\n'
        string += "currentaction:"         + str(self.currentaction)         + '\n'
        string += "currenttag:"            + str(self.currenttag)            + '\n'
        string += "currentactontime:"      + str(self.currentactiontime)     + '\n'
        string += "nrretry:"               + str(self.retry)                 + '\n'
        return string
        
    def __repr__(self):
        return self.__str__()
