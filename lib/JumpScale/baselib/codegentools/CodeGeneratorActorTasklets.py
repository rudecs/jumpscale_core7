from JumpScale import j

from .CodeGeneratorBase import CodeGeneratorBase

NOTGENSTR = "##DONOTGENERATE##"

tasklets = {}
tasklets["default"] = """
def main(j, params, service, tags, tasklet):
    params.result=None
    return params

def match(j, params, service, tags, tasklet):
    return True
"""

tasklets["modeldelete"] = """
def main(j, params, service, tags, tasklet):
    #delete
    appname={appname}
    actorname={actorname}
    modelname={modelname}
    params.result=None
    return params

def match(j, params, service, tags, tasklet):
    return True
"""

tasklets["modelget"] = """
def main(j, params, service, tags, tasklet):
    #delete
    appname="{appname}"
    actorname="{actorname}"
    modelname="{modelname}"
    modeldb=j.apps.{appname}.{actorname}.models.{modelname}
    try:
        obj=modeldb.get(params.id)
    except Exception,e:
        if str(e).find("Key value store doesnt have a value for key") != -1:
            #did not find
            params.result=False
            return params

    params.result={}
    params.result["JSModelobject"]=obj.obj2dict()
    params.result["JSModeltype"]="{appname}__{actorname}__{modelname}"
    return params

def match(j, params, service, tags, tasklet):
    return True
"""


tasklets["modelcreate"] = """
def main(j, params, service, tags, tasklet):
    #create
    appname="{appname}"
    actorname="{actorname}"
    modelname="{modelname}"
    modeldb=j.apps.{appname}.{actorname}.models.{modelname}

    ddict=j.tools.json.decode(params.data)
    obj=modeldb.new()
    obj2=j.core.osis.dict2JSModelobject(obj,ddict)
    modeldb.set(obj2)
    params.result=[obj2.id,obj2.guid]
    return params

def match(j, params, service, tags, tasklet):
    return True
"""

tasklets["modelupdate"] = """
def main(j, params, service, tags, tasklet):
    #set
    #appname="{appname}"
    #actorname="{actorname}"
    #modelname="{modelname}"
    modeldb=j.apps.{appname}.{actorname}.models.{modelname}

    ddict=j.tools.json.decode(params.data)
    obj=modeldb.new()
    obj2=j.core.osis.dict2JSModelobject(obj,ddict)
    modeldb.set(obj2)
    params.result=[obj2.id,obj2.guid]
    return params

def match(j, params, service, tags, tasklet):
    return True
"""

tasklets["modelfind"] = """
def main(j, params, service, tags, tasklet):
    #find
    appname="{appname}"
    actorname="{actorname}"
    modelname="{modelname}"
    modeldb=j.apps.{appname}.{actorname}.models.{modelname}
    res=modeldb.find(params.query)
    if len(res)>100:
        params.result="TOO MANY RESULTS, MAX 100"
    else:
        params.result=res
    return params

def match(j, params, service, tags, tasklet):
    return True
"""
tasklets["modellist"] = """
def main(j, params, service, tags, tasklet):
    #list
    from JumpScale.core.Shell import ipshellDebug,ipshell
    print("DEBUG NOW model list")
    ipshell()
    appname="{appname}"
    actorname="{actorname}"
    modelname="{modelname}"
    modeldb=j.apps.{appname}.{actorname}.models.{modelname}
    res=modeldb.find(params.query)
    if len(res)>100:
        params.result="TOO MANY RESULTS, MAX 100"
    else:
        params.result=res
    return params

def match(j, params, service, tags, tasklet):
    return True
"""

tasklets["modeldatatables"] = """
def main(j, params, service, tags, tasklet):
    #list
    from JumpScale.core.Shell import ipshellDebug,ipshell
    print("DEBUG NOW model datatables")
    ipshell()
    
    appname="{appname}"
    actorname="{actorname}"
    modelname="{modelname}"
    modeldb=j.apps.{appname}.{actorname}.models.{modelname}
    res=modeldb.find(params.query)
    if len(res)>100:
        params.result="TOO MANY RESULTS, MAX 100"
    else:
        params.result=res
    return params

def match(j, params, service, tags, tasklet):
    return True
"""

tasklets["modelnew"] = """
def main(j, params, service, tags, tasklet):
    #new
    appname="{appname}"
    actorname="{actorname}"
    modelname="{modelname}"
    modeldb=j.apps.{appname}.{actorname}.models.{modelname}
    obj=modeldb.new()
    modeldb.set(obj)
    params.result={}
    params.result["JSModelobject"]=obj.obj2dict()
    params.result["JSModeltype"]="{appname}__{actorname}__{modelname}"
    return params

def match(j, params, service, tags, tasklet):
    return True
"""


class CodeGeneratorActorTasklets(CodeGeneratorBase):

    def __init__(self, spec, typecheck=True, dieInGenCode=True, overwrite=False, codepath=None):
        overwrite = False  # can never overwrite
        CodeGeneratorBase.__init__(self, spec, typecheck, dieInGenCode)
        self.codepath = j.system.fs.joinPaths(codepath, "methodtasklets")
        j.system.fs.createDir(self.codepath)
        self.type = "tasklets"
        self.overwrite = overwrite

    def generate(self):
        spec = self.spec

        for method in self.spec.methods:

            path = j.system.fs.joinPaths(self.codepath, "method_%s" % method.name)
            j.system.fs.createDir(path)

            path = j.system.fs.joinPaths(self.codepath, "method_%s" % method.name,
                                         "5_%s_%s.py" % (spec.actorname, method.name))

            path2 = j.system.fs.joinPaths(self.codepath, "method_%s" % method.name, "5_main.py")
            if j.system.fs.exists(path2):
                j.system.fs.moveFile(path2, path)

            if j.system.fs.exists(path):
                # content=j.system.fs.fileGetContents(path)
                # if content.find(NOTGENSTR) != -1:
                    # path=j.system.fs.joinPaths(j.core.portal.active.codepath,spec.appname,spec.actorname,method.name,"_5_main.py")
                path = None

            if path != None and str(path) != "":
                # lets also check there are no files in it yet

                if len(j.system.fs.listFilesInDir(j.system.fs.getDirName(path))) == 0:
                    templ = "default"
                    tags = j.core.tags.getObject(method.tags)
                    if tags.tagExists("tasklettemplate"):
                        templ = tags.tagGet("tasklettemplate").strip().lower()
                    if templ not in tasklets:
                        raise RuntimeError("Cannot find tasklet template %s in \n%s" % (templ, method))
                    content = tasklets[templ]
                    if templ.find("model") == 0:  # is used for templates for crud methods
                        content = content.replace("{appname}", spec.appname)
                        content = content.replace("{actorname}", spec.actorname)
                        content = content.replace("{modelname}", method.name.split("_", 2)[1])
                    j.system.fs.writeFile(path, content)

        return self.getContent()
