from JumpScale import j
import JumpScale.baselib.remote
import sys
# import importlib
import imp
try:
    import ujson as json
except:
    import json

import JumpScale.baselib.redis
import copy
import time
import JumpScale.baselib.webdis

from fabric.api import hide
import time

redis=j.clients.redis.getRedisClient("127.0.0.1", 9999)

class Node():
    def __init__(self,name,args={}):
        self.model=j.core.admin.hrd.getDictFromPrefix("node.%s"%name)
        self.ssh=None
        self.args=args

    def executeCmds(self,cmds,die=True,insandbox=False):
        scriptRun=self.getScriptRun()
        out=scriptRun.out
        for line in cmds.split("\n"):
            if line.strip()!="" and line[0]!="#":
                self.log("execcmd",line)
                if insandbox:
                    line2="source /opt/jsbox/activate;%s"%line 
                else:
                    line2=line               
                try:                    
                    out+="%s\n"%self.ssh.run(line2)
                except BaseException as e:
                    if die:
                        self.raiseError("execcmd","error execute:%s"%line,e)

    def killProcess(self,filterstr,die=True):
        found=self.getPids(filterstr)
        for item in found:
            self.log("killprocess","kill:%s"%item)
            try:
                self.ssh.run("kill -9 %s"%item)
            except Exception as e:
                if die:
                    self.raiseError("killprocess","kill:%s"%item,e)

    def getPids(self,filterstr,die=True):
        self.log("getpids","")
        with hide('output'):
            try:
                out=self.ssh.run("ps ax")
            except Exception as e:
                if die:
                    self.raiseError("getpids","ps ax",e)
        found=[]
        for line in out.split("\n"):
            if line.strip()!="":
                if line.find(filterstr)!=-1:
                    line=line.strip()
                    found.append(int(line.split(" ")[0]))   
        return found

    def deployssh(self):
        self.connectSSH()
        keyloc="/root/.ssh/id_dsa.pub"
        
        if not j.system.fs.exists(path=keyloc):
            if j.console.askYesNo("do you want to generate new local ssh key, if you have one please put it there manually!"):
                do=j.system.process.executeWithoutPipe
                do("ssh-keygen -t dsa")
            else:
                j.application.stop()
        key=j.system.fs.fileGetContents(keyloc)
        self.ssh.ssh_authorize("root",key)

    def jpackageStop(self,name,filterstr,die=True):
        self.log("jpackagestop","%s (%s)"%(name,filterstr))
        try:
            self.ssh.run("source /opt/jsbox/activate;jpackage stop -n %s"%name)
        except Exception as e:
            if die:
                self.raiseError("jpackagestop","%s"%name,e)
        
        found=self.getPids(filterstr)
        if len(found)>0:
            for item in found:
                try:
                    self.ssh.run("kill -9 %s"%item)            
                except:
                    pass

    def jpackageStart(self,name,filterstr,nrtimes=1,retry=1):
        found=self.getPids(filterstr)
        self.log("jpackagestart","%s (%s)"%(name,filterstr))
        for i in range(retry):
            if len(found)==nrtimes:
                return
            scriptRun=self.getScriptRun()
            try:
                self.ssh.run("source /opt/jsbox/activate;jpackage start -n %s"%name)  
            except Exception as e:
                if die:
                    self.raiseError("jpackagestart","%s"%name,e)                          
            time.sleep(1)
            found=self.getPids(filterstr)
        if len(found)<nrtimes:
            self.raiseError("jpackagestart","could not jpackageStart %s"%name)

    def serviceStop(self,name,filterstr):
        self.log("servicestop","%s (%s)"%(name,filterstr))
        try:
            self.ssh.run("sudo stop %s"%name)
        except:
            pass
        found=self.getPids(filterstr)
        scriptRun=self.getScriptRun()
        if len(found)>0:
            for item in found:
                try:
                    self.ssh.run("kill -9 %s"%item)            
                except:
                    pass
        found=self.getPids(filterstr)
        if len(found)>0:
            self.raiseError("servicestop","could not serviceStop %s"%name)

    def serviceStart(self,name,filterstr,die=True):
        self.log("servicestart","%s (%s)"%(name,filterstr))
        found=self.getPids(filterstr)
        if len(found)==0:
            try:
                self.ssh.run("sudo start %s"%name)          
            except:
                pass            
        found=self.getPids(filterstr)
        if len(found)==0 and die:
            self.raiseError("servicestart","could not serviceStart %s"%name)            

    def serviceReStart(self,name,filterstr):
        self.serviceStop(name,filterstr)
        self.serviceStart(name,filterstr)

    def raiseError(self,action,msg,e=None):
        scriptRun=self.getScriptRun()
        scriptRun.state="ERROR"
        if e!=None:
            msg="Stack:\n%s\nError:\n%s\n"%(j.errorconditionhandler.parsePythonErrorObject(e),e)
            scriptRun.state="ERROR"
            scriptRun.error+=msg

        for line in msg.split("\n"):
            toadd="%-10s: %s\n" % (action,line)
            scriptRun.error+=toadd
            print(("**ERROR** %-10s:%s"%(self.name,toadd)))
        self.lastcheck=0
        j.admin.setNode(self)
        j.admin.setNode(self)
        raise RuntimeError("**ERROR**")

    def log(self,action,msg):
        out=""
        for line in msg.split("\n"):
            toadd="%-10s: %s\n" % (action,line)
            print(("%-10s:%s"%(self.name,toadd)))
            out+=toadd

    def setpasswd(self,passwd):
        #this will make sure new password is set
        self.log("setpasswd","")
        cl=j.tools.expect.new("sh")
        if self.args.seedpasswd=="":
           self.args.seedpasswd=self.findpasswd()
        try:
            cl.login(remote=self.name,passwd=passwd,seedpasswd=None)
        except Exception as e:
            self.raiseError("setpasswd","Could not set root passwd.")

    def findpasswd(self):
        self.log("findpasswd","find passwd for superadmin")
        cl=j.tools.expect.new("sh")
        for passwd in j.admin.rootpasswds:
            try:            
                pass
                cl.login(remote=self.name,passwd=passwd,seedpasswd=None)
            except Exception as e:
                self.raiseError("findpasswd","could not login using:%s"%passwd,e)
                continue
            self.passwd=passwd
            j.admin.setNode(self)
        return "unknown"

    def check(self):
        j.base.time.getTimeEpoch()

    def connectSSH(self):
        ip=self.model["ip"]
        port=self.model["port"]
        passwd=self.model["passwd"]
        self.ssh=j.remote.cuisine.connect(ip,port,passwd)

        # if j.system.net.pingMachine(self.args.remote,1):
        #     self.ip=self.args.remote
        # else:
        #     j.events.opserror_critical("Could not ping node:'%s'"% self.args.remote)

        return self.ssh

    def uploadFromCfgDir(self,ttype,dest,additionalArgs={}):
        dest=j.dirs.replaceTxtDirVars(dest)
        cfgdir=j.system.fs.joinPaths(self._basepath, "cfgs/%s/%s"%(j.admin.args.cfgname,ttype))

        additionalArgs["hostname"]=self.name

        cuapi=self.ssh
        if j.system.fs.exists(path=cfgdir):
            self.log("uploadcfg","upload from %s to %s"%(ttype,dest))

            tmpcfgdir=j.system.fs.getTmpDirPath()
            j.system.fs.copyDirTree(cfgdir,tmpcfgdir)
            j.dirs.replaceFilesDirVars(tmpcfgdir)
            j.application.config.applyOnDir(tmpcfgdir,additionalArgs=additionalArgs)

            items=j.system.fs.listFilesInDir(tmpcfgdir,True)
            done=[]
            for item in items:
                partpath=j.system.fs.pathRemoveDirPart(item,tmpcfgdir)
                partpathdir=j.system.fs.getDirName(partpath).rstrip("/")
                if partpathdir not in done:
                    cuapi.dir_ensure("%s/%s"%(dest,partpathdir), True)
                    done.append(partpathdir)
                try:            
                    cuapi.file_upload("%s/%s"%(dest,partpath),item)#,True,True)  
                except Exception as e:
                    j.system.fs.removeDirTree(tmpcfgdir)
                    self.raiseError("uploadcfg","could not upload file %s to %s"%(ttype,dest))
            j.system.fs.removeDirTree(tmpcfgdir)

    def upload(self,source,dest):
        args=j.admin.args
        if not j.system.fs.exists(path=source):
            self.raiseError("upload","could not find path:%s"%source)
        self.log("upload","upload %s to %s"%(source,dest))
        # from IPython import embed
        # print "DEBUG NOW implement upload in Admin"  #@todo
        # embed()
    
        for item in items:
            partpath=j.system.fs.pathRemoveDirPart(item,cfgdir)
            partpathdir=j.system.fs.getDirName(partpath).rstrip("/")
            if partpathdir not in done:
                print((cuapi.dir_ensure("%s/%s"%(dest,partpathdir), True)))
                done.append(partpathdir)            
            cuapi.file_upload("%s/%s"%(dest,partpath),item)#,True,True)                       

    def __repr__(self):
        roles=",".join(self.roles)
        return ("%-10s %-10s %-50s %-15s %-10s %s"%(self.gridname,self.name,roles,self.ip,self.host,self.enabled))

    __str__=__repr__
