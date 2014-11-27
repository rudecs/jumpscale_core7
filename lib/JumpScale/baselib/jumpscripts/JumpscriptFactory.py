from JumpScale import j
import time
import imp
import linecache
import inspect
import JumpScale.baselib.redis
import multiprocessing
from .Jumpscript import Jumpscript

class JumpscriptFactory:

    """
    """
    def __init__(self):
        self.jumpscripts={}
        j.system.fs.createDir(j.system.fs.joinPaths(j.dirs.tmpDir,"jumpscripts"))

    def getJSClass(self):
        return Jumpscript

    def load(self,path):
        for item in j.system.fs.listFilesInDir(path,True,filter="*.py"):
            basename=j.system.fs.getBaseName(item)
            if basename[0]=="_":
                continue
            basename=basename.replace(".py","")
            organization,actor=basename.split("__",1)
            js=Jumpscript(path=item,organization=organization,actor=actor)
            key="%s__%s"%(js.organization,js.actor)
            self.jumpscripts[key]=js

    def execute(self,organization,actor,action,args):
        key="%s__%s"%(organization,actor)
        if key not in self.jumpscripts:
            j.events.inputerror_critical("Cannot find jumpscript:'%s/%s'"%(organization,actor))
        js= self.jumpscripts[key]
        js.execute(action, **args)