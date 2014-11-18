from JumpScale import j
from .OSISInstance import *


class OSIS:

    """
    """

    def __init__(self):
        self.dict2object = j.code.dict2JSModelobject  # was dict2object
        self.osisInstances = {}

    def get(self, appname, actorname, modelname, modelClass=None, db=None, index=False, indexer=None):
        fullname = "%s_%s_%s" % (appname, actorname, modelname)
        if fullname in self.osisInstances:
            return self.osisInstances[fullname]
        self.osisInstances[fullname] = OSISInstance(appname, actorname, modelname, modelClass, db, index, indexer)
        return self.osisInstances[fullname]

    def getNoDB(self, appname, actorname, modelname, modelClass=None):
        fullname = "%s_%s_%s" % (appname, actorname, modelname)
        if fullname in self.osisInstances:
            return self.osisInstances[fullname]
        self.osisInstances[fullname] = OSISInstanceNoDB(appname, actorname, modelname, modelClass)
        return self.osisInstances[fullname]

    def getRemoteOsisDB(self, appname, actorname, modelname, modelClass=None):
        fullname = "%s_%s_%s" % (appname, actorname, modelname)
        if fullname in self.osisInstances:
            return self.osisInstances[fullname]
        self.osisInstances[fullname] = OSISRemoteOSISInstance(appname, actorname, modelname, modelClass)
        return self.osisInstances[fullname]

    def _findModels(self, appname, actorname="*", modelname="*"):
        result = []
        for fullname in list(self.osisInstances.keys()):
            appname2, actorname2, modelname2 = fullname.split("_", 2)

            o = self.osisInstances[fullname]
            if (appname == "*" or appname == appname2) and (actorname == "*" or actorname == actorname2) \
               and (modelname == "*" or modelname == modelname2):
                result.append(o)
        return result

    def _get(self, appname, actorname, modelname):
        return "%s_%s_%s" % (appname, actorname, modelname)

    def destroy(self, appname, actorname="*", modelname="*"):
        """
        destroy all objects & indexes with mentioned names
        """
        objects = self._findModels(appname, actorname, modelname)
        for o in objects:
            o.destroy()
            fullname = "%s_%s_%s" % (o.appname, o.actorname, o.modelname)
            print("destroy model: %s" % fullname)

    def rebuildindex(self, appname, actorname="*", modelname="*"):
        """
        destroy all objects & indexes with mentioned names
        """
        objects = self._findModels(appname, actorname, modelname)
        for o in objects:
            o.rebuildindex()

    # def objectToText4Index(self, obj, modelSpec):
    #     from JumpScale.core.Shell import ipshellDebug, ipshell
    #     print "DEBUG NOW use object2dict4index"
    #     ipshell()

    #     result = self._objectToText4Index(obj, modelSpec, root=True)
    #     result = result.replace("\n", ",")
    #     return result

    def inputNormalizeList(self,param):
        """
        comma separated string becomes list
        list gets checked, if all int then returnformat=1
        list gets checked, if all str, then returnformat=2
        @return (returnformat,list)
        """
        if j.basetype.string.check(param):
            param=[item.strip() for item in param.split(",")]

        try:
            param2=[int(item) for item in param]
            formatt=1
        except:
            formatt=2
            param2=param
            #no int
        return (formatt,param2)


    def _normalize(self, sstr):
        sstr = sstr.replace(",", "")
        sstr = sstr.replace(":", " ")
        sstr = sstr.replace("\n", "\\n")
        sstr = sstr.replace("\t", " ")
        sstr = sstr.replace(";", " ")
        sstr = sstr.replace("?", " ")
        return sstr


    # def _objectToText4Index(self,obj,modelSpec,result="",path="",root=False):


        # if modelSpec in ["int","str","float","bool"]:
            # if str(obj) != "":
                # if path[-1]==".":
                    # path=path[:-1]
                # result+="%s:%s\n" % (path,obj)
            # return result
        # for prop in modelSpec.properties:
            # item=obj.__dict__["_P_%s"%prop.name]
            # if prop.type in ["int","str","float","bool"]:
                # if prop.type=="str":
                    # val=normalize(item)
                # else:
                    # val=str(item)
                # if val != "" and root != True:
                    # result+="%s:%s\n" % (path+prop.name,val)
            # else:
                # ttype,specsub=j.core.specparser.getSpecFromTypeStr(modelSpec.appname,modelSpec.actorname,prop.type)
                # is list or dict or subobject
                # if ttype=="list":
                    # for item2 in item:
                        # result+=self._objectToText4Index(item2,specsub,result,path+prop.name+".")
                # elif ttype=="dict":
                    # for key in item.keys():
                        # item2=item[key]
                        # result+=self._objectToText4Index(item2,specsub,result,path+prop.name+".")
                # elif ttype=="enum":
                    # result+="%s:%s\n" % (path+prop.name,item)
                # elif ttype=="object":
                    # result=+self._objectToText4Index(item,specsub,result,path+prop.name+".")
                # else:
                    # raise RuntimeError("not implemented, cannot process subobject when indexing object %s" % obj.id)
        # return result
