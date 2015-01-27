from JumpScale import j

import JumpScale.baselib.packInCode
import JumpScale.baselib.remote.cuisine
import json

class JPackageRemoteFactory(object):
    def sshPython(self, jp, node):
        return RemotePython(jp,node)

    def sshLua(self, jp, node):
        return RemoteLua(jp,node)

def _sshConnect(node):
    sshHRD = j.application.getAppInstanceHRD("node.ssh.key", node)
    ip = sshHRD.get("param.machine.ssh.ip")
    port = sshHRD.get("param.machine.ssh.port")
    keyhrd=j.application.getAppInstanceHRD("sshkey",sshHRD.get('param.ssh.key.name'))
    j.remote.cuisine.fabric.env["key"] = keyhrd.get('param.ssh.key.priv')
    cl=j.remote.cuisine.connect(ip,port)
    return cl

class RemotePython(object):
    def __init__(self, jp, node):
        self.node = node
        self.jp = jp
        self.cl = _sshConnect(node)

    def execute(self, action):
        codegen=j.tools.packInCode.get4python()

        #put hrd on dest system
        hrddestfile="%s/%s.%s.%s.hrd"%(j.dirs.getHrdDir(system=True),self.jp.domain,self.jp.name,self.jp.instance)
        codegen.addHRD("jphrd",self.jp.hrd,hrddestfile)

        #put action file on dest system
        actionfile="%s/%s__%s.py"%(j.dirs.getJPActionsPath(self.node),self.jp.name,self.jp.instance)
        actionfiledest="%s/%s__%s__%s.py"%(j.dirs.getJPActionsPath(system=True),self.jp.domain,self.jp.name,self.jp.instance)
        codegen.addPyFile(actionfile,path2save=actionfiledest)
        # from ipdb import set_trace;set_trace()
        toexec=codegen.get()

        cwd = j.system.fs.getParent(j.system.fs.getParent(j.system.fs.getParent(hrddestfile)))

        # create a .git dir so the directory is seen as a git config repo
        # if not self.cl.file_exists("%s/.git"%cwd):
        #     cmd = "cd %s; mkdir .git" %(cwd)
        #     self.cl.run(cmd)
        # if not self.cl.file_exists("%s/jp"%cwd):
        #     cmd = "cd %s; mkdir jp" %(cwd)
        #     self.cl.run(cmd)

        # install hrd and action file on remote system
        tmploc = '/tmp/exec.py'
        self.cl.file_write(tmploc, toexec)
        cmd = "jspython %s" % tmploc
        self.cl.run(cmd)
        # then run the jpackage command on the remote system
        # cmd = 'cd %s; jpackage %s -n %s -i %s --remote' % (cwd, action, self.self.jp.name, self.self.jp.instance)
        cmd = 'jpackage %s -n %s -i %s --remote' % (action, self.jp.name, self.jp.instance)
        self.cl.run(cmd)
        del j.remote.cuisine.fabric.env["key"]


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