from JumpScale import j
import imp

from types import MethodType

class ActionManager:
    """
    the action manager is responsible for executing the actions linked to a jpackages
    """

    def __init__(self,jp):
        # print "init actions for %s"%jp
        self._jpackage=jp
        self._actions={}
        self._done={}                

        def load(path):
            name=j.system.fs.getBaseName(path)
            name=name[:-3]

            md5 = j.tools.hash.md5_string(path)
            modname = "JumpScale.baselib.jpackages.%s" % md5
            # print path

            if not j.system.fs.exists(path=path):
                raise RuntimeError("Could not find path:%s for actionmanager."%path)
            
            module = imp.load_source(modname, path)
            self._actions[name]= module.main

            attribname = name.replace(".","_")
            self.__dict__[attribname] = self._getActionMethod(name)

        classpath=jp.getPathMetadata()
        for actionname in j.packages.getActionNamesClass():
            path=j.system.fs.joinPaths(classpath,"actions","%s.py"%actionname)
            load(path)

        instancepath=jp.getPathInstance()
        if jp.instance!=None and j.system.fs.exists(path=j.system.fs.joinPaths(instancepath,"actions")):
            if j.system.fs.exists(instancepath):
                for actionname in j.packages.getActionNamesInstance():
                    path=j.system.fs.joinPaths(instancepath,"actions","%s.py"%actionname)
                    load(path)        

    def clear(self):
        self._done={}
        
    def _getActionMethod(self,name):
        found=False
        for item in ["kill","start","stop","monitor"]:
            if name.find(item)!=-1:
                found=True

        if found==True:
            C="""
def method(self{args}):
    print "%s : action:'{name}'"%self._jpackage
    result=self._actions['{name}'](j,self._jpackage{args})
    return result"""

        else:
            C="""
def method(self{args}):
    key="%s_%s_{name}"%(self._jpackage.domain,self._jpackage.name)
    if self._done.has_key(key):
        #print "already executed %s"%key
        return True
    print "%s : action:'{name}'"%self._jpackage
    result=self._actions['{name}'](j,self._jpackage{args2})
    self._done[key]=True
    return result"""

        args=""
        args2=""

        if name=="code.link" or name=="code.update":
            args=",force=True"
            args2=",force=force"

        elif name=="install.download":
            args=",expand=True,nocode=False"
            args2=",expand=expand,nocode=nocode"

        elif name=="upload":
            args=",onlycode=False"
            args2=",onlycode=onlycode"

        elif name=="data.export" or name=="data.import":
            args=",url=None"       
            args2=",url=url"

        elif name=="monitor.up.net":
            args=",ipaddr='localhost'"       
            args2=",ipaddr=ipaddr"

        C=C.replace("{args}",args)
        C=C.replace("{args2}",args2)
        C=C.replace("{name}",name)
        # print C
        exec(C)
        return MethodType(method, self, ActionManager)
