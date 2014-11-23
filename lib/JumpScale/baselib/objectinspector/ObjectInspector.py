
from JumpScale import j


    # api codes
# 4 function with params
# 7 ???
# 8 property

import inspect

class MethodDoc():
    def __init__(self):
        self.params=None
        self.comments=""

class ClassDoc():
    def __init__(self,classobj,location):
        self.location=location
        self.methods={}
        self.comments=inspect.getdoc(classobj)
        module=inspect.getmodule(classobj)
        self.path=inspect.getabsfile(module)

    def addMethod(self,name,method):
        try:
            source = inspect.getsource(method)
        except:
            self.errors += 'h5. Error trying to add %s source in %s.\n' % (name, self.location)
            
        inspected = inspect.getargspec(method)
        comments=inspect.getdoc(method)
            
        params = ""
        for param in inspected.args:
            if param.lower().strip() != "self":
                params = params + param + ","
        params = params[:-1]

        md=MethodDoc()
        md.params=params
        md.comments=comments
        md.linenr=inspect.getsourcelines(method)[1]
        md.name=name
        self.methods[name]=md

        return source,params

    def write(self,dest):
        dest2=j.system.fs.joinPaths(dest, self.location.split(".")[1],"%s.wiki"%self.location)
        out="h3. %s\n"%self.location
        if self.path.find("JumpScale")!=-1:        
            path=self.path.split("JumpScale",1)[1]
        elif self.path.find("python.zip")!=-1:
            path="python.zip/%s"%self.path.split("python.zip",1)[1]
        else:
            # from IPython import embed
            # print "DEBUG NOW write objectinspector, found new location"
            # embed()
            ##TODO
            pass
        out += " `Source <https://github.com/Jumpscale/jumpscale_core/tree/master/lib/JumpScale%s>`_  \n\n" % (path)
        if self.comments!=None:
            out+="\n%s\n\n"%self.comments

        keys=list(self.methods.keys())
        keys.sort()
        for name in keys:
            method=self.methods[name]
            out+="h4. %s\n\n"%(name)
            out+="* params: %s\n"%(method.params)
            out+="* path:%s (line:%s)\n\n"%(path,method.linenr)
            if method.comments!=None:
                out+="%s\n\n"%method.comments

        destdir= j.system.fs.getDirName(dest2)
        j.system.fs.createDir(destdir)
        j.system.fs.writeFile(filename=dest2,contents=out)

        catname=destdir.strip("/").split("/")[-1]
        C="""
h2. j.$name

{{rst:
.. toctree::
   :maxdepth: 2
   :glob:  

$names
}}

"""        
        names=""
        for item in j.system.fs.listFilesInDir(destdir,False,"j.*.wiki"):
            n=j.system.fs.getBaseName(item)[:-5]
            names+="   %s\n"%n

        C=C.replace("$names",names)
        C=C.replace("$name",catname)
        j.system.fs.writeFile(filename=j.system.fs.joinPaths(destdir,"%s.wiki"%catname),contents=C)
        




class ObjectInspector():

    """
    functionality to inspect objectr structure and generate apifile
    """

    def __init__(self):
        self.apiFileLocation = j.system.fs.joinPaths(j.dirs.cfgDir, "codecompletionapi", "jumpscale.api")
        j.system.fs.createDir(j.system.fs.joinPaths(j.dirs.cfgDir, "codecompletionapi"))
        self.classDocs={}

    def importAllLibs(self,ignore=[],base="/opt/code/github/jumpscale/jumpscale_core/lib/JumpScale/"):
        towalk=[]
        towalk.append("baselib")
        towalk.append("lib")
        towalk.append("grid")
        towalk.append("portal")
        errors="h3. errors while trying to import libraries\n\n"
        for item in towalk:
            
            path="%s/%s"%(base,item)
            for modname in j.system.fs.listDirsInDir(path,False,True,True):
                if modname not in ignore:
                    toexec="import JumpScale.%s.%s"%(item,modname)
                    print(toexec)
                    try:
                        exec(toexec)
                    except Exception as e:
                        print(("COULD NOT IMPORT %s"%toexec))
                        errors+="**%s**\n\n"%toexec
                        errors+="%s\n\n"%e
        return errors


    def generateDocs(self,dest,ignore=[]):
        self.errors=self.importAllLibs(ignore=ignore)
        self.inspect()
        j.system.fs.writeFile(filename="%s/errors.wiki"%dest,contents=self.errors)
        self.writeDocs(dest)


    def _processMethod(self, name,method,path,classobj):
        if path not in self.classDocs:
            self.classDocs[path]=ClassDoc(classobj,path)
        obj=self.classDocs[path]
        return obj.addMethod(name,method)

    def inspect(self, objectLocationPath="j"):
        """
        walk over objects in memory and create code completion api in jumpscale cfgDir under codecompletionapi
        @param object is start object
        @param objectLocationPath is full location name in object tree e.g. j.system.fs , no need to fill in
        """
        if not j.basetype.string.check(objectLocationPath):
            raise RuntimeError("objectLocationPath needs to be string")
        print(objectLocationPath)
        if objectLocationPath.find("_object.")==-1:
            obj= eval(objectLocationPath)
            try:
                self.processObject(obj,objectLocationPath)
            except Exception as e:
                pass

    def processObject(self,obj,objectLocationPath="j"):
        for dictitem in dir(obj):
            objectLocationPath2 = "%s.%s" % (objectLocationPath, dictitem)
            print(objectLocationPath2)
            if len(dictitem)>1:
                if dictitem.find("__getChildObjectsExamples")!=-1:
                    getChildObjectsExamples = eval("%s" % objectLocationPath2)
                    res=getChildObjectsExamples()
                    
                    for objectLocationPath2,obj2 in list(res.items()):
                        self.processObject(obj2,objectLocationPath2)
                
            if len(dictitem)>1 and dictitem[0] != "_":
                print(objectLocationPath2)
                objectNew = None
                try:
                    # objectNew = eval("%s" % objectLocationPath2)
                    objectNew= eval("obj.%s"%(dictitem))
                except:                    
                    print(("COULD NOT EVAL %s" % objectLocationPath2))
                if objectNew == None:
                    pass
                elif dictitem.upper() == dictitem:
                    # is special type or constant
                    objectLocationPath2 = "%s.%s" % (objectLocationPath, dictitem)
                    # print "special type: %s" % objectLocationPath2
                    j.system.fs.writeFile(self.apiFileLocation, "%s?7\n" % objectLocationPath2, True)
                elif str(type(objectNew)).find("'instance'") != -1 or str(type(objectNew)).find("<class") != -1 or str(type(objectNew)).find("'classobj'") != -1:
                    j.system.fs.writeFile(self.apiFileLocation, "%s?8\n" % objectLocationPath2, True)
                    # print "class or instance: %s" % objectLocationPath2
                    self.inspect(objectLocationPath2)
                elif str(type(objectNew)).find("'instancemethod'") != -1 or str(type(objectNew)).find("'function'") != -1\
                        or str(type(objectNew)).find("'staticmethod'") != -1 or str(type(objectNew)).find("'classmethod'") != -1:
                    # is instancemethod
                    source, params = self._processMethod(dictitem,objectNew,objectLocationPath,obj)
                    objectLocationPath2 = "%s.%s" % (objectLocationPath, dictitem)
                    # print "instancemethod: %s" % objectLocationPath2
                    j.system.fs.writeFile(self.apiFileLocation, "%s?4(%s)\n" % (objectLocationPath2, params), True)
                elif str(type(objectNew)).find("'str'") != -1 or str(type(objectNew)).find("'type'") != -1 or str(type(objectNew)).find("'list'") != -1\
                    or str(type(objectNew)).find("'bool'") != -1 or str(type(objectNew)).find("'int'") != -1 or str(type(objectNew)).find("'NoneType'") != -1\
                        or str(type(objectNew)).find("'dict'") != -1 or str(type(objectNew)).find("'property'") != -1 or str(type(objectNew)).find("'tuple'") != -1:
                    # is instancemethod
                    objectLocationPath2 = "%s.%s" % (objectLocationPath, dictitem)
                    # print "property: %s" % objectLocationPath2
                    j.system.fs.writeFile(self.apiFileLocation, "%s?8\n" % objectLocationPath2, True)
                else:
                    print((str(type(objectNew)) + " " + objectLocationPath2))

    def writeDocs(self,path):
        for key,doc in list(self.classDocs.items()):
            doc.write(path)

        C="""
h2. Lib docs

{{rst:
.. toctree::
   :maxdepth: 2
   :glob:  

$names
}}

"""        
        names=""
        for item in j.system.fs.listDirsInDir(path,False,True):
            names+="   %s/%s\n"%(item,item)

        C=C.replace("$names",names)

        j.system.fs.writeFile(filename=j.system.fs.joinPaths(path,"index.wiki"),contents=C)
        

