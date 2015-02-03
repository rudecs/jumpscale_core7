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
        self.cl = self._connect(node)

    def _negotiateConnection(self,target):
        nodes = self._getAllNodes()
        for kind,nodes in nodes.iteritems():
            for node in nodes:
                if node == target:
                    return kind
        return None

    def _getAllNodes(self):
        jps = ["node.ssh.key","node.ms1","node.kvm"]
        nodes = {}
        for jp in jps:
            nodes[jp] = []
            instances = j.application.getAppHRDInstanceNames(jp)
            nodes[jp].extend(instances)
        return nodes

    def _generateUniq(self,name):
        epoch = int(time.time())
        return "%s_%s_%s" % (epoch,self.jp.name,name)

    def _connect(self, node):
        connKind = self._negotiateConnection(node)
        if connKind is None:
            raise RuntimeError("No node found")
        if connKind in ["node.ssh.key","node.ms1"]:
            return self._sshConnect(node,connKind)
        elif connKind in ['node.kvm']:
            return self._kvmConnect(node,connKind)

    def _sshConnect(self,node,kind):
        c = j.remote.cuisine
        sshHRD = j.application.getAppInstanceHRD(kind, node)
        self.ip = sshHRD.get("param.machine.ssh.ip")
        self.port = sshHRD.get("param.machine.ssh.port")
        self.keyname = sshHRD.get('param.ssh.key.name')
        self._keyhrd = j.application.getAppInstanceHRD("sshkey",self.keyname)
        c.fabric.env["key"] = self._keyhrd.get('param.ssh.key.priv')
        cl = c.connect(self.ip,self.port)
        return cl

    def _kvmConnect(self,node,kind='node.kvm'):
        kvmHRD = j.application.getAppInstanceHRD(kind, node)
        hostType = kvmHRD.get("param.hostnode.type")
        hostInstance = kvmHRD.get("param.hostnode.instance")
        hostCl = self._sshConnect(hostInstance,hostType)

        config = self.executeCode("j.system.platform.kvm.getConfig('%s')" % node)
        vmHRD = j.core.hrd.get(content=config)
        vmIP = vmHRD.get("bootstrap.ip")
        vmLogin = vmHRD.get("bootstrap.login")
        vmPasswd = vmHRD.get("bootstrap.passwd")

        # forward ssh of vm to outside
        rule = hostCl.run("iptables -L -n -v | grep 'tcp dpt:2222'")
        if rule != "":
            ss = rule.split(":")
            ip = ss[len(ss)-2]
            cmd = "iptables -t nat -D PREROUTING -p tcp --dport 2222 -j DNAT --to-destination %s:22" % ip
            hostCl.run(cmd)
        cmd = "iptables -t nat -A PREROUTING -p tcp --dport 2222 -j DNAT --to-destination %s:22" % vmHRD.get("bootstrap.ip")
        hostCl.run(cmd)

        c = j.remote.cuisine.fabric.env['password'] = vmHRD.get("bootstrap.passwd")
        cl=cl.connect(vmIP,2222)
        return cl

    def copyTree(self, source, dest ,sshkey=None, port=None, ignoredir=[".egg-info",".dist-info"],ignorefiles=[".egg-info"]):
        print("copy %s %s" % (source,dest))
        if not j.do.exists(source):
            raise RuntimeError("copytree:Cannot find source:%s"%source)
        excl=""
        for item in ignoredir:
            excl+="--exclude '*%s*/' "%item
        for item in ignorefiles:
            excl+="--exclude '*%s*' "%item
        excl+="--exclude '*.pyc' "
        excl+="--exclude '*.bak' "
        excl+="--exclude '*__pycache__*' "
        if j.do.isDir(source):
            if dest[-1]!="/":
                dest+="/"
            if source[-1]!="/":
                source+="/"
        destdir = dest.split(':')[1]
        if not self.cl.file_exists(destdir):
            cmd = "mkdir -p %s" % destdir
            self.cl.run(cmd)

        ssh=""
        if sshkey is None:
            sshkey = self._keyhrd.get("param.ssh.key.priv")
        if port is None:
            port = self.port
        keyloc = "/tmp/%s" % self._generateUniq('id_dsa')
        j.system.fs.writeFile(keyloc,sshkey)
        j.system.fs.chmod(keyloc,0o600)
        ssh += "-e 'ssh -i %s -p %s'" % (keyloc,port)


        cmd="rsync -vP %s -a --no-compress --max-delete=0 %s %s %s"%(ssh,excl,source,dest)
        j.do.execute(cmd)
        j.system.fs.remove(keyloc)

    def executeCode(self,code):
        code = """
from JumpScale import j
%s
""" % code
        codeloc = "/tmp/%s" % self._generateUniq('exec.py')
        self.cl.file_write(codeloc, code)
        cmd = "jspython %s" % codeloc
        return self.cl.run(cmd)

    def executeJP(self, action):
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
        with self.cl.fabric.context_managers.hide('running'):
            self.cl.file_write(codeloc, code)
            cmd = "jspython %s" % codeloc
            print "RUN %s" % action
            self.cl.run(cmd)


class RemoteLua(object):
    def __init__(self, jp, node):
        self.node = node
        self.jp = jp
        self.cl = _sshConnect(node)

    def executeJP(self, action):
        # add hrd content into actions file
        # the hrd is converted into a lua table
        dictHRD = self.self.jp.hrd.getHRDAsDict()
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
