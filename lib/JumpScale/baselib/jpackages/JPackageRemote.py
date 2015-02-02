from JumpScale import j

import JumpScale.baselib.packInCode
import JumpScale.baselib.remote.cuisine
import json
import time

class JPackageRemoteFactory(object):

    def sshPython(self, jp, node):
        return RemotePython(jp,node)

    def sshLua(self, jp, node):
        return RemoteLua(jp,node)


class RemotePython(object):
    def __init__(self, jp, node):
        self.node = node
        self.jp = jp
        self.ip = None
        self.port = None
        self.keyname = None
        self._keyhrd = None
        self.cl = self._sshConnect(node)


    def _generateUniq(self,name):
        epoch = int(time.time())
        return "%s_%s_%s" % (epoch,self.jp.name,name)

    def _sshConnect(self,node):
        sshHRD = j.application.getAppInstanceHRD("node.ssh.key", node)
        self.ip = sshHRD.get("param.machine.ssh.ip")
        self.port = sshHRD.get("param.machine.ssh.port")
        self.keyname = sshHRD.get('param.ssh.key.name')
        self._keyhrd = j.application.getAppInstanceHRD("sshkey",self.keyname)
        j.remote.cuisine.fabric.env["key"] = self._keyhrd.get('param.ssh.key.priv')
        cl=j.remote.cuisine.connect(self.ip,self.port)
        return cl

    def copyTree(self,src,dest):
        keyloc = "/tmp/%s" % self._generateUniq('id_dsa')
        j.system.fs.writeFile(keyloc,self._keyhrd.get("param.ssh.key.priv"))
        j.system.fs.chmod(keyloc,0o600)
        destdir = dest.split(':')[1]
        if not self.cl.file_exists(destdir):
            cmd = "mkdir -p %s" % destdir
            self.cl.run(cmd)
        print("send %s to %s" %(src,dest))
        j.do.copyTree(src,dest,sshkey=keyloc)

    def execute(self, action):
        action = action.replace("_","") # make sure the action name is correcte
        codegen=j.tools.packInCode.get4python()

        actionfile="%s.py" % self.jp.actionspath
        actionContent = j.system.fs.fileGetContents(actionfile)
        codegen.code +="""
class JPackageInstanceMock(object):
    def __init__(self, domain,name,instance):
        self.domain = domain
        self.name = name
        self.instance = instance
"""
        codegen.code +="""
class JPackageMock(object):

    def __init__(self,hrd,domain,name,instance):
        self.hrd = hrd
        self.instance = instance
        self.jp = JPackageInstanceMock(domain,name,instance)

    def getLogPath(self):
        logpath=j.system.fs.joinPaths(j.dirs.logDir,"startup", "%s_%s_%s.log" % (self.jp.domain, self.jp.name,self.jp.instance))
        return logpath

    def getHRDPath(self,node=None):
        if j.packages.type=="c":
            hrdpath = "%s/%s.%s.hrd" % (j.dirs.getHrdDir(node=node), self.jp.name, self.jp.instance)
        else:
            hrdpath = "%s/%s.%s.%s.hrd" % (j.dirs.getHrdDir(), self.jp.domain, self.jp.name, self.jp.instance)
        return hrdpath

    def isInstalled(self):
        hrdpath = self.getHRDPath()
        if j.system.fs.exists(hrdpath):
            return True
        return False

    def getTCPPorts(self,deps=True, *args, **kwargs):
        ports = set()
        for process in self.getProcessDicts():
            for item in process["ports"]:
                if isinstance(item, basestring):
                    moreports = item.split(";")
                elif isinstance(item, int):
                    moreports = [item]
                for port in moreports:
                    if isinstance(port, int) or port.isdigit():
                        ports.add(int(port))
        return list(ports)


    def getPriority(self):
        processes = self.getProcessDicts()
        if processes:
            return processes[0].get('prio', 100)
        return 199

    def getProcessDicts(self,deps=True,args={}):
        counter = 0
        defaults={"prio":10,"timeout_start":10,"timeout_start":10,"startupmanager":"tmux"}
        musthave=["cmd","args","prio","env","cwd","timeout_start","timeout_start","ports","startupmanager","filterstr","name","user"]

        procs=self.hrd.getListFromPrefixEachItemDict("process",musthave=musthave,defaults=defaults,aredict=['env'],arelist=["ports"],areint=["prio","timeout_start","timeout_start"])
        for process in procs:
            counter+=1

            process["test"]=1

            if process["name"].strip()=="":
                process["name"]="%s_%s"%(self.hrd.get("jp.name"),self.hrd.get("jp.instance"))

            if self.hrd.exists("env.process.%s"%counter):
                process["env"]=self.hrd.getDict("env.process.%s"%counter)

            if not isinstance(process["env"],dict):
                raise RuntimeError("process env needs to be dict")

        return procs
\n
        """
        codegen.addHRD(name="hrd",hrd=self.jp.hrd)
        codegen.code += actionContent
        codegen.code += "\naction = Actions()\n"
        codegen.code += "action.jp_instance = JPackageMock(hrd,'%s','%s','%s')\n" %(self.jp.domain,self.jp.name,self.jp.instance)
        codegen.code += "action.%s()\n"%action

        code = codegen.get()
        codeloc = "/tmp/%s" % self._generateUniq('exec.py')
        self.cl.file_write(codeloc, code)
        cmd = "jspython %s" % codeloc
        print "RUN %s" % action
        self.cl.run(cmd)


class RemoteLua(object):
    def __init__(self, jp, node):
        self.node = node
        self.jp = jp
        self.cl = _sshConnect(node)

    def execute(self, action):
        # add hrd content into actions file
        # the hrd is converted into a lua table
        dictHRD = self.self.jp.hrd.getHRDAsDict()
        from ipdb import set_trace;set_trace()
        jsonHRD = json.dumps(dictHRD)
        content = """local json = require 'json'
        local hrd = json.decode.decode('%s')

        """ % jsonHRD

        #put action file on dest system
        actionfile="%s/%s__%s.lua"%(j.dirs.getJPActionsPath(node=self.node),self.self.jp.name,self.self.jp.instance)
        content += j.system.fs.fileGetContents(actionfile)
        # add the call to the wanted function into the lua file
        # and pass the args table we construct from the hrd
        content+= "\n%s(hrd)"%action
        actionfiledest="%s/%s__%s.lua"%(j.dirs.tmpDir,self.self.jp.name,self.self.jp.instance)
        self.cl.file_write(actionfiledest,content)
        j.system.fs.writeFile("/opt/code/action.lua",content)
        cmd = 'lua %s' % (actionfiledest)
        self.cl.run(cmd)
        del j.remote.cuisine.fabric.env["key"]
