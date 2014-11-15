from JumpScale import j
import platform
import urllib2
import gzip
import os
import tarfile
import sys
import copy
import time

class PortApp(j.code.classGetBase()):
    def __init__(self):
        self.descr=""
        self.url=""
        self.cat=""
        self.buildactive=0
        self.buildrepo=0
        self.exe=""
        self.auth=False
        self.dest=""
        self.name=""
        self.installed=False
        self.processnames=""
        self.shutdowncmd=""
        self.configdir=""
        self.category=""
        
    def _update(self):
        self.configdir=j.system.fs.joinPaths(j.dirs.varDir,"portapps",self.name)
        self.configdir=self.configdir.replace("/","\\")
        
    def _replaceArgs(self,txt):
        txt=txt.replace("{appdir}",self.dest)        
        txt=txt.replace("{configdir}",self.configdir)
        return txt
        
    def kill(self):
        self._update()
        def shutdown():
            if self.shutdowncmd.strip()<>"":
                cmd=self._replaceArgs(self.shutdowncmd)
                try:
                    j.system.process.execute(cmd)
                except:
                    pass
            if self.name=="skype":
                time.sleep(3)

        for procid in j.system.windows.listRunningProcesses():
            procid=str(procid.lower().strip())
            for name in self.processnames.split(","):
                if procid.find(name)<>-1:
                    pid=j.system.windows.getPidOfProcess(procid)
                    if pid>100:
                        shutdown()
                        try:
                            j.system.process.kill(pid)
                        except Exception,e:
                            print "could not kill %s %s" % (pid,name)
                            print e
        
    def start(self,args="",agent=False,kill=True):
        self._update()
        if kill:
            self.kill()
        app=j.clients.portapps.getFromRepo(self.name)
        j.system.fs.createDir(self.configdir)
        if not j.system.fs.exists(app.dest):
            q.client.portapps.install(app.name)
        dest=self._replaceArgs(app.exe)
        cmd=dest            
        if args<>"":
            cmd=cmd+" "+args
        print "Execute %s" % cmd
        j.system.process.execute(dest)

class PortApps(j.code.classGetBase()):
    
    def __init__(self):
        self.portappsrepo={}
        self.portappsactive={}
        j.dirs.varDir=j.system.fs.joinPaths(j.dirs.baseDir,"var")
        self._load()        
    
    def updatefromrepo(self):
        """
        list all apps
        """
        destcfg=j.system.fs.joinPaths(j.dirs.cfgDir,"portappslist.cfg")
        self._download("http://bitbucket.org/incubaid/portapps/raw/default/cfg/list.cfg",\
                       destcfg,expand=False)
        ini=j.tools.inifile.open(destcfg)
        for section in ini.getSections():
            pa=PortApp()
            pa.name=section
            pa.descr=ini.getValue(section,"description",default="")
            pa.url=ini.getValue(section,"url")
            pa.cat=ini.getValue(section,"category",default="unknown")
            pa.build=int(ini.getValue(section,"build",default=999999))
            pa.exe=ini.getValue(section,"exe",default="")
            pa.category=ini.getValue(section,"category",default="").strip().lower()
            pa.dest=ini.getValue(section,"dest",default="")
            if pa.dest.strip()=="":
                pa.dest=j.system.fs.joinPaths(j.dirs.baseDir,"portapps",pa.name)
            pa.auth=ini.getValue(section,"auth",default=False)
            pa.processnames=ini.getValue(section,"processnames",default="")
            pa.shutdowncmd=ini.getValue(section,"shutdowncmd",default="")            
            pa.installed=False
            pa._update()
            self.portappsrepo[section]=pa   
        print "metadata portapps updated"

    def reset(self):
        self.killall()
        destcfg=j.system.fs.joinPaths(j.dirs.cfgDir,"portappslist.cfg")
        j.system.fs.remove(destcfg)
        destcfg=j.system.fs.joinPaths(j.dirs.varDir,"portapps.data")
        j.system.fs.remove(destcfg)
        appsdir=j.system.fs.joinPaths(j.dirs.baseDir,"portapps")
        j.system.fs.removeDirTree(appsdir)
        self.update()
    
    def save(self):
        destcfg=j.system.fs.joinPaths(j.dirs.varDir,"portapps.data")
        data=j.tools.json.encode(self.obj2dict())
        j.system.fs.writeFile(destcfg,data)

    def _load(self):
        destcfg=j.system.fs.joinPaths(j.dirs.varDir,"portapps.data")
        if j.system.fs.exists(destcfg):
            data=j.system.fs.fileGetContents(destcfg)
            data=j.tools.json.decode(data)
            for name in data["portappsactive"].keys():
                datasub=data["portappsactive"][name]
                pa=PortApp()
                j.code.dict2object(pa,datasub)
                self.portappsactive[name]=pa
            for name in data["portappsrepo"].keys():
                datasub=data["portappsrepo"][name]
                pa=PortApp()
                j.code.dict2object(pa,datasub)
                self.portappsrepo[name]=pa
            
    def _download(self,url,to="",expand=True):
        j.system.fs.changeDir(j.dirs.tmpDir)
        if expand:
            toTgz="portappexpanded.tgz"
        else:
            toTgz=to
        print 'Downloading %s \n to %s' % (url,to)
        handle = urllib2.urlopen(url)
        progress=0
        with open(toTgz, 'wb') as out:
            while True:
                progress+=1
                if progress>100:
                    print"#",
                    progress=0
                data = handle.read(1024)
                if len(data) == 0: break
                out.write(data)
        handle.close()
        out.close()
        if expand:
            self._expand(toTgz,to)
            
            
    def exists(self,name):
        return self.portappsactive.has_key(name)
    
    def get(self,name):
        """
        @return get metadata object
        """
        if self.portappsrepo=={}:
            self.updatefromrepo()
        if self.portappsactive.has_key(name):
            return self.portappsactive[name]            
        if self.portappsrepo.has_key(name):
            return self.portappsrepo[name]
        else:
            raise RuntimeError("Could not find portapp %s" % name)

    def getFromRepo(self,name):
        """
        @return get metadata object
        """
        if self.portappsrepo=={}:
            self.updatefromrepo()
        if self.portappsrepo.has_key(name):
            return self.portappsrepo[name]
        else:
            raise RuntimeError("Could not find portapp %s" % name)

    def getActive(self):
        result=[]
        for name in self.portappsactive.keys():
            pa=self.portappsactive[name]  
            result.append(pa)
        return result        

    def getRepoApps(self):
        result=[]
        for name in self.portappsrepo.keys():
            pa=self.portappsrepo[name]  
            result.append(pa)
        return result    
        
    def _delete(self,path):
        j.system.fs.removeDirTree(path)
    
    def _expand(self,path,destdir,ddelete=True):
        j.system.fs.changeDir(j.dirs.tmpDir)
        self._delete(destdir)    
        self._delete('portappexpanded.tar')
        if j.system.platformtype.isWindows():            
            cmd="gzip -d %s" % path
            j.system.process.execute(cmd)
        else:
            #@todo use jumpscale everywhere we can (was copied from an installer where jumpscale could not be used)
            handle = gzip.open(path)
            with open('portappexpanded.tar', 'w') as out:
                for line in handle:
                    out.write(line)
            out.close()
            handle.close()
        
        t = tarfile.open('portappexpanded.tar', 'r')
        t.extractall(destdir)    
        t.close()
        
        if ddelete:
            self._delete(path)
            self._delete("portappexpanded.tar")                          
            
    def install(self,name="",dest="",updaterepo=False):
        if updaterepo:
            self.updatefromrepo()
        if self.portappsrepo=={}:
            self.updatefromrepo()
        if name=="":
            names=j.console.askChoiceMultiple([item for item in j.clients.portapps.list().split("\n") if item.strip()<>""])
            names=[item.split(" ")[0].strip() for item in names]
        else:
            names=[name]
        for name in names:
            paActive=copy.deepcopy(self.get(name))
            if self.portappsrepo.has_key(name):
                pa=self.portappsrepo[name]
                to=j.system.fs.joinPaths(j.dirs.baseDir,"portapps",name)
                if not j.system.fs.exists(to):
                    j.system.fs.createDir(to)
                    paActive.installed=False
                if paActive.installed==False or int(paActive.build)<int(pa.build):
                    print "download portapp %s, this can take a while please wait." % name
                    self._download(pa.url,to)
                    print "download done for %s" %name
                
                #remember downloaded app
                paActive.installed=True
                paActive.dest=to
                paActive.exe=pa.exe
                if str(pa.build)=="999999":
                    paActive.build=1
                self.portappsactive[name]=paActive
            else:
                raise RuntimeError("Could not find app %s" % name)
        self.save()
        
    def killall(self):
        self.updatefromrepo()
        apps=self.getRepoApps()
        for app in apps:
            app.kill()        

    def update(self):   
        self.killall()
        apps=self.getActive()
        for app in apps:
            self.install(app.name)