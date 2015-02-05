from JumpScale import j

import JumpScale.baselib.packInCode
import JumpScale.baselib.remote.cuisine
import json
import time

class JPackageRemoteFactory(object):
    def __init__(self):
        self.node = None
        self.remotePython = None
        self.remoteLua = None

    def sshPython(self, jp, node):
        if self.node != node or self.remotePython is None:
            self.remotePython = RemotePython(jp,node)
            self.node = node

        self.remotePython.jp = jp
        return self.remotePython

    def sshLua(self, jp, node):
        if self.node != node or self.remoteLua is None:
            self.remoteLua = RemoteLua(jp,node)
            self.node = node

        self.remoteLua.jp = jp
        return self.remoteLua

    def getAllNodes(self):
        jps = ["node.ssh.key","node.ms1","node.kvm"]
        nodes = {}
        for jp in jps:
            nodes[jp] = []
            instances = j.application.getAppHRDInstanceNames(jp)
            nodes[jp].extend(instances)
        return nodes

class RemoteBase(object):
    def __init__(self, jp, node):
        self.node = node
        self.jp = jp
        self.ip = None
        self.port = None
        self.login = None
        self.passwd = None
        self.key = None
        self.keyname = None
        self._keyhrd = None
        self.connection = self._connect(node)

    def _generateUniq(self,name):
        epoch = int(time.time())
        return "%s_%s_%s" % (epoch,self.jp.name,name)

    def _negotiateConnection(self,target):
        nodes = j.packages.remote.getAllNodes()
        for kind,nodes in nodes.iteritems():
            for node in nodes:
                if node == target:
                    return kind
        return None

    def _connect(self, node):
        connKind = self._negotiateConnection(node)
        if connKind is None:
            raise RuntimeError("No node found for %s" % node)
        client = None
        if connKind in ["node.ssh.key","node.ms1"]:
            client = self._sshConnect(node,connKind)
        elif connKind in ['node.kvm']:
            client = self._kvmConnect(node,connKind)

        if not j.application.debug:
            client.fabric.state.output['running'] = False
            client.fabric.state.output['out'] = False

        return client

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
        """
        This function establish a connection to a kvm machine
        First it connects to the host and forward a port of the host to the ssh port of the vm in order to expose the vm
        Then it connects to the vm thought ssh
        """
        # connection to the host machine
        kvmHRD = j.application.getAppInstanceHRD(kind, node)
        hostType = kvmHRD.get("param.hostnode.type")
        hostInstance = kvmHRD.get("param.hostnode.instance")
        hostCl = self._sshConnect(hostInstance,hostType)
        hostIp = self.ip
        hostPort = self.port

        vmIp = kvmHRD.get("param.machine.ssh.ip")
        self.passwd = kvmHRD.get("param.machine.ssh.passwd")
        self.login = kvmHRD.get("param.machine.ssh.login")
        self.key = kvmHRD.get("param.machine.ssh.key")
        self.port = 2222

        # remove current port forward if any
        cmd = "ps ax | grep -v '/bin/bash -l -c' | grep 'ssh -f -N -L' > /tmp/ssh"
        hostCl.run(cmd)
        res = hostCl.run("cat /tmp/ssh")
        processes = res.splitlines()
        for line in processes:
            pid = line.strip().split(" ")[0]
            cmd = "kill %s" %pid
            hostCl.run(cmd, warn_only=True) # warn_only=True, don't crash if process doesn't exist
        # expose vm
        cmd = "ssh -f -N -L %s:localhost:22  %s" % (self.port,vmIp)
        hostCl.run(cmd)

        c = j.remote.cuisine
        c.fabric.env['password'] = self.passwd
        c.fabric.env['login'] = self.login
        c.fabric.env['key'] = self.key
        c.fabric.env['ip'] = hostIp
        c.fabric.env['port'] = self.port
        c.fabric.env['shell'] = "/bin/sh -c"
        return c.connect(hostIp,self.port)

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
        if not self.connection.file_exists(destdir):
            cmd = "mkdir -p %s" % destdir
            self.connection.run(cmd)

        ssh=""
        if sshkey is None:
            sshkey = self._keyhrd.get("param.ssh.key.priv")
        if port is None:
            port = self.port
        keyloc = "/tmp/%s" % self._generateUniq('id_dsa')
        j.system.fs.writeFile(keyloc,sshkey)
        j.system.fs.chmod(keyloc,0o600)
        ssh += "-e 'ssh -i %s -p %s'" % (keyloc,port)

        verbose = "-q"
        if j.application.debug:
            verbose = "-v"
        cmd="rsync -P %s %s -a --max-delete=0 %s %s %s"%(verbose,ssh,excl,source,dest)
        j.do.execute(cmd)
        j.system.fs.remove(keyloc)

    def writeFile(self, dest, content, sshkey=None,port=None):
        ssh=""
        if sshkey is None:
            if self.key is not None:
                sshkey = self.key
            elif self._keyhrd is not None:
                sshkey = self._keyhrd.get("param.ssh.key.priv")
            elif self.keyname is not None:
                keyhrd = j.application.getAppInstanceHRD("sshkey",self.keyname)
                sshkey = keyhrd.get('param.ssh.key.priv')

        port = self.port if self.port is not None else 22
        keyloc = "/tmp/%s" % self._generateUniq('id_dsa')
        j.system.fs.writeFile(keyloc,sshkey)
        j.system.fs.chmod(keyloc,0o600)
        ssh += "-i %s -P %s" % (keyloc,port)

        fileLoc = "/tmp/%s" % self._generateUniq('content')
        j.system.fs.writeFile(fileLoc,content)
        dest = "root@%s:%s" % (self.ip,dest)

        verbose = "-q"
        if j.application.debug:
            verbose = "-v"

        cmd="scp %s %s %s %s"%(verbose,ssh,fileLoc,dest)
        print "Send file : %s" % cmd
        j.do.executeInteractive(cmd)
        j.system.fs.remove(keyloc)
        j.system.fs.remove(fileLoc)

    def executeCode(self, code, client=None):
        if client is None:
            client = self.connection

        code = """
from JumpScale import j
%s
""" % code
        codeloc = "/tmp/%s" % self._generateUniq('exec.py')
        self.writeFile(codeloc,code)
        cmd = "jspython %s" % codeloc
        return client.run(cmd)


class RemotePython(RemoteBase):
    def __init__(self, jp, node):
        super(RemotePython,self).__init__(jp=jp,node=node)


    def executeJP(self, action, client=None):
        if client is None:
            client = self.connection

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
        self.writeFile(codeloc,code)
        cmd = "jspython %s" % codeloc
        print "RUN %s" % action
        client.run(cmd)


class RemoteLua(RemoteBase):
    def __init__(self, jp, node):
        super(RemoteLua,self).__init__(jp=jp,node=node)

    def executeJP(self, action, client=None):
        if client is None:
            client = self.connection
        # add hrd content into actions file
        # the hrd is converted into a lua table
        dictHRD = self.jp.hrd.getHRDAsDict()
        jsonHRD = json.dumps(dictHRD)
        content = """local json = require 'json'
        local hrd = json.decode.decode('%s')

        """ % jsonHRD

        #put action file on dest system
        actionfile="%s/%s__%s.lua"%(j.dirs.getJPActionsPath(node=self.node),self.jp.name,self.jp.instance)
        content += j.system.fs.fileGetContents(actionfile)
        # add the call to the wanted function into the lua file
        # and pass the args table we construct from the hrd
        content+= "\n%s(hrd)"%action
        actionfiledest="%s/%s__%s.lua"%(j.dirs.tmpDir,self.jp.name,self.jp.instance)
        self.writeFile(actionfiledest,content)
        j.system.fs.writeFile("/opt/code/action.lua",content)
        cmd = 'lua %s' % (actionfiledest)
        client.run(cmd)
        del j.remote.cuisine.fabric.env["key"]
