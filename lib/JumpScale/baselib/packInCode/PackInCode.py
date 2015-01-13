
from JumpScale import j

import json as json

class packInCodeFactory():
    def get4python(self):
        return packInCodePython()

class packInCodePython():
    def __init__(self):
        self.code="""
from JumpScale import j
import JumpScale.baselib.packInCode
codegen=j.tools.packInCode.get4python()

"""

    def _serialize(self,c):
        c=c.replace("\"","\\\"")
        return c

    def unserialize(self,c):
        c=c.replace("\\\"","\"")
        return c        

    def addBlock(self,name,block):
        C="""
$name=\"\"\"
$block
\"\"\"

"""     
        C=C.replace("$block",self._serialize(block))      
        C=C.replace("$name",name)  
        self.code+=C    
        


    def addDict(self,name,ddict):
        code=json.dumps(obj=ddict, sort_keys=True,indent=4, separators=(',', ': '))
        self.code+="%s=\"\"\"\n%s\n\"\"\"\n\n"%(name,code)

    def addHRD(self,name,hrd,path):
        C="""
hrdtmp=\"\"\"
$hrd
\"\"\"
hrdtmp=codegen.unserialize(hrdtmp)
$name=j.core.hrd.get(content=hrdtmp)
$name.path=\"$path\"
$name.save()
"""
        C=C.replace("$name",name)
        C=C.replace("$hrd",self._serialize(str(hrd)))
        C=C.replace("$path",path)
        self.code+="%s\n"%C

    def addPyFile(self,path2add,path2save=None):
        if path2save==None:
            path2save=path2add
        code=j.do.readFile(path2add)
        C="""
codetmp=\"\"\"
$code
\"\"\"
j.do.createDir(j.do.getParent(\"$path2save\"))
codetmp=codegen.unserialize(codetmp)
j.do.writeFile(\"$path2save\",codetmp)
"""
        C=C.replace("$code",self._serialize(code))
        C=C.replace("$path2save",str(path2save))
        self.code+="%s\n"%C

    def save(self,path):
        j.do.writeFile(path,self.code)

    def get(self):
        return self.code