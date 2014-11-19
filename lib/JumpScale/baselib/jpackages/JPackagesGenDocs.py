from JumpScale import j

class JPackagesGenDocs:

    def __init__(self):
        self.outpath="%s/apps/gridportal/base/jpackagedocs"%j.dirs.baseDir
        self.docs=JPdata()
        self.docsLastGen=0
        self.getHrdLists=self.docs.getHrdLists
        self.getDuplicateFiles=self.docs.getDuplicateFiles

    def getDocs(self,refresh=False):
        if self.docsLastGen<j.base.time.getEpochAgo("-1h"):
            msg= "regenerate docs for jpackages"
            j.packages.log(msg, category='doc.generate', level=5)

            jpackagedirs=[item for item in j.system.fs.listDirsInDir("/opt/code",recursive=True) if j.system.fs.getBaseName(item).find("jp_")==0]
            for jpackagedir in jpackagedirs:
                hrdfiles=j.system.fs.listFilesInDir(jpackagedir,True,"main.hrd")
                for hrdfile in hrdfiles:
                    ql=j.system.fs.getDirName(hrdfile,levelsUp=3)
                    if ql=="unstable":
                        domain=j.system.fs.getDirName(hrdfile,levelsUp=4)
                        if domain[0:3]=="jp_":
                            domain=domain[3:]
                        packagename=j.system.fs.getDirName(hrdfile,levelsUp=2)
                        version=j.system.fs.getDirName(hrdfile,levelsUp=1)
                        path=j.system.fs.getParent(hrdfile)
                        path=j.system.fs.getParent(path)
                        jp=self.docs.addJPackage(ql,domain,packagename,version,path)
            self.docsLastGen=j.base.time.getTimeEpoch()

        return self.docs


class JPdata():
    def __init__(self):
        self.domains={}

    def _getData(self,refresh=False):
        return j.packages.docGenerator.getDocs(refresh=refresh)

    def addDomain(self,ql,domain):
        self.domains[domain]=Domain(ql,domain)

    def addJPackage(self,ql,domain,packagename,version,path):
        if domain not in self.domains:
            self.addDomain(ql,domain)
        domaino=self.domains[domain]
        return domaino.addJPackage(ql,domain,packagename,version,path)

    def walk(self,method,params={}):
        keys=list(self.domains.keys())
        keys.sort()
        
        for dom in keys:
            domain=self.domains[dom]
            keys2=list(domain.packages.keys())
            keys2.sort()
            for name in keys2:
                jp=domain.packages[name]
                # print "walk %s :: %s"%(domain.name,name)
                params=method(jp,params)
        return params

    def existsPackage(self,domain,name,version):
        self._getData()
        key= "%s_%s_%s"%(domain,name,version)
        if domain not in self.domains:            
            return False
        domain=self.domains[domain]
        if key not in domain.packages:
            return False
        return True

    def getPackage(self,domain,name,version):
        if not self.existsPackage(domain,name,version):
            raise RuntimeError("Cannot find package:%s %s %s"%(domain,name,version))
        key= "%s_%s_%s"%(domain,name,version)
        domain=self.domains[domain]
        return domain.packages[key]

    def getPackageFromKey(self,key):
        for domname in list(self.domains.keys()):
            domain=self.domains[domname]            
            if key in domain.packages:
                return domain.packages[key]
        raise RuntimeError("Cannot find package: %s"%key)

    def checkErrors(self,path):
        self.checkDuplicateFiles(path)

    def getDuplicateFiles(self):
        self._getData()
        params={}
        params["dups"]=[]
        def checkF(jp,params):
            items=jp.getBlobFiles()
            if items != []:
                return params
        params=self.walk(checkF,params)

    # def writeJPackageInfo(self,path):
    #     params={}
    #     params["path"]=path
    #     def write(jp,params):
    #         jp.writeJPackageInfo(params["path"])
    #         return params
    #     params=data.walk(write,params)

    def getHrdLists(self,refresh=False):
        """
        @return hrdlistPerPackage,hrdlist
        """
        data=self._getData(refresh=refresh)

        params={}
        def hrdlistM(jp,params):
            for hrdparam in list(jp.hrdvars.keys()):
                jpkey,path=jp.hrdvars[hrdparam]
                params[hrdparam]=(jpkey,path)
            return params
        hrdlist=data.walk(hrdlistM,params)

        keys=list(hrdlist.keys())
        keys.sort()

        hrdPerJpackage={}
        for hrdkey in keys:
            jpkey,hrdpath=hrdlist[hrdkey]
            jp=self.getPackageFromKey(jpkey)
            if jpkey not in hrdPerJpackage:
                hrdPerJpackage[jpkey]=[]
            hrdPerJpackage[jpkey].append((hrdkey,hrdpath))

        jpkeys=list(hrdPerJpackage.keys())
        jpkeys.sort()
        out="@usedefault\n\nh2. list of hrd keys\n\n"
        for jpkey in jpkeys:
            jp=self.getPackageFromKey(jpkey)
            out+="h3. %s\n"%jp.getKeyTitle()
            link="[%s|/system/JPackageShow?domain=%s&name=%s&version=%s]"%(jp.name,jp.domain,jp.name,jp.version)
            out+="* jpackage:%s\n"%link
            out+="* path:%s\n"%jp.path
            out+="||hrdkey||system val||hrd path||\n"
            for hrdkey,hrdpath in hrdPerJpackage[jpkey]:
                out+="|%s|$(%s)|%s|\n"%(hrdkey,hrdkey,hrdpath)
            out+="\n"
        out=j.application.config.applyOnContent(out)

        out2="@usedefault\n\nh2. list of hrd keys\n\n"
        out2+="||hrdkey||system val||jpackage||\n"
        for jpkey in jpkeys:
            jp=self.getPackageFromKey(jpkey)
            for hrdkey,hrdpath in hrdPerJpackage[jpkey]:
                link="[%s|/system/JPackageShow?domain=%s&name=%s&version=%s]"%(jp.name,jp.domain,jp.name,jp.version)
                out2+="|%s|$(%s)|%s|\n"%(hrdkey,hrdkey,link)
        out2=j.application.config.applyOnContent(out2)
        return out,out2

    def writeHrdList(self,path):
        hrdlistPerPackage,hrdlist=self.getHrdList()

        path2=j.system.fs.joinPaths(self.outpath,"hrdlistPerPackage.wiki")
        j.system.fs.writeFile(path2,out)

        path2=j.system.fs.joinPaths(self.outpath,"hrdlist.wiki")
        j.system.fs.writeFile(path2,out)

    def __repr__(self):
        out=""
        keys=list(self.domains.keys())
        keys.sort()
        for item in keys:
            out+="domain:%s\n%s\n\n"%(item,self.domains[item])
        return out

    __str__=__repr__


class Domain():
    def __init__(self,ql,name):
        self.ql=ql
        self.name=name
        self.packages={}

    def addJPackage(self,ql,domain,packagename,version,path):
        jp=JPackage(ql,domain,packagename,version,path)
        key=jp.getKey()
        if key in self.packages:
            prevjp=self.packages[key]
            newer=False
            # from IPython import embed
            # print "DEBUG NOW check previous jpackage, only when newer put"
            # embed()
            if newer==False:
                return prevjp
            
        self.packages[key]=jp
        return jp

    def __repr__(self):
        out=""
        keys=list(self.packages.keys())
        keys.sort()
        for item in keys:
            out+="      %s\n"%(self.packages[item])
        return out

    __str__=__repr__


class JPackage():
    def __init__(self,ql,domain,packagename,version,path):
        self.ql=ql
        self.domain=domain
        self.name=packagename
        self.version=version
        self.path=path
        self.hrdvars={}
        self.hrdfiles={}
        self._init()

    def getKey(self):
        return "%s_%s_%s"%(self.domain,self.name,self.version)

    def getKeyTitle(self):
        return "%s %s (%s)"%(self.name,self.domain,self.version)

    def _init(self):
        path="%s/%s/%s"%(self.path,"hrd","main.hrd")
        if not j.system.fs.exists(path):
            raise RuntimeError("Could not find main.hrd : %s"%path)

        pathdescr="%s/%s"%(self.path,"description.wiki")
        if not j.system.fs.exists(path):
            raise RuntimeError("Could not find %s"%path)

        hrd=j.core.hrd.getHRD(path)

        try:
            if hrd.get("jp.name") != self.name:
                hrd.set("jp.name",self.name)
        except:
            j.packages.reportError("Could not load hrd info for name for :%s"%self.getKey)

        try:
            if hrd.get("jp.domain") != self.domain:
                hrd.set("jp.domain",self.domain)
        except:
            j.packages.reportError("Could not load hrd info for domain for :%s"%self.getKey)

        self._loadHrdInfo()

    def getBlobFiles(self):
        """
        @return [[md5,path]]
        """
        result=[]
        path="%s/%s"%(self.path,"blob_generic.info")
        if not j.system.fs.exists(path):
            return []
            raise RuntimeError("Could not find blob_generic.info for %s"%self)
        content=j.system.fs.fileGetContents(path)
        state="start"
        for line in content.split("\n"):
            line=line.strip()
            if line=="" or line[0]=="#":
                continue
            if line.find("======") != -1:
                state="do"
                continue
            if state=="start":
                continue
            #now we are in relevant section
            if line.find("|")==-1:
                raise RuntimeError("Error in blobfile, needs to have | at this location: %s"%line)
            splitted=line.split("|")
            if len(splitted) != 2:
                raise RuntimeError("Error in blobfile, needs to have 1 | at this location: %s"%line)
            result.append(splitted)
        return result

    def getJpackageObject(self):
        return j.packages.get(self.domain, self.name, self.version)

    def getDescr(self):
        path="%s/%s"%(self.path,"description.wiki")
        if not j.system.fs.exists(path):
            return ""
        descr=j.system.fs.fileGetContents(path)
        descr=j.application.config.applyOnContent(descr)

        jp=self.getJpackageObject()
        
        descr=jp.hrd.applyOnContent(descr)

        return descr

        
    def _getActiveHrdFiles(self):
        if self.hrdfiles=={}:
            path="%s/%s"%(self.path,"hrdactive")
            if not j.system.fs.exists(path):
                j.system.fs.createDir(path)
                j.system.fs.writeFile("%s/.empty"%path,".")
                
            hrdfiles=j.system.fs.listFilesInDir(path,True,"*.hrd")
            hrdfiles=[item for item in hrdfiles if j.system.fs.getBaseName(item)[0] != "_"]
            result={}
            for item in hrdfiles:
                result[j.system.fs.getBaseName(item)]=item
            self.hrdfiles=result
        return self.hrdfiles

    def _loadHrdInfo(self,name=None):
        if name==None:
            for name in list(self._getActiveHrdFiles().keys()):
                self._loadHrdInfo(name)
        else:
            path=self._getActiveHrdFiles()[name]
            content=j.system.fs.fileGetContents(path)
            for line in content.split("\n"):
                line=line.strip()
                if line=="" or line.find("=")==-1:
                    continue
                name=line.split("=")[0]
                name=name.strip()
                self.hrdvars[name]=(self.getKey(),path)

    # def getDocPath(self,path,name=""):
    #     if name=="":
    #         path=j.system.fs.joinPaths(path,self.ql,self.domain,self.name,"%s.wiki"%self.name)        
    #     else:
    #         path=j.system.fs.joinPaths(path,self.ql,self.domain,self.name,"%s.wiki"%name)        
    #     j.system.fs.createDir(j.system.fs.getDirName(path))
    #     return path

    # def writeHrdDoc(self,path):
    #     out=""
    #     for name in self.listActiveHrd().keys():
    #         out+=self.getHrdDoc(name)
    #     if out != "":
    #         path=self.getDocPath(path,"activehrd_%s"%name)
    #         j.system.fs.writeFile(path,out)

    def __repr__(self):
        out="%s"%self.getKeyTitle()
        return out

    __str__=__repr__

