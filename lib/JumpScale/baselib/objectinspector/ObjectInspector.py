
from JumpScale import j


    # api codes
# 4 function with params
# 7 ???
# 8 property

import inspect

class Arg():
    def __init__(self,name,defaultvalue):
        self.name=name
        self.defaultvalue=defaultvalue

    def __str__(self):        
        out=""
        if self.defaultvalue!=None:
            out+="- %s = %s\n"%(self.name,self.defaultvalue)
        else:
            out+="- %s\n"%(self.name)
        return out

    def __repr__(self):
        return self.__str__()


class MethodDoc():
    def __init__(self,method,name,classdoc):
        self.classdoc=classdoc
        self.params=[]

        inspected = inspect.getargspec(method)
        params = ""
        if inspected.defaults!=None:
            counter=len(inspected.defaults)-len(inspected.args)
        else:
            counter=-99999
            
        for param in inspected.args:
            if inspected.defaults!=None and counter>-1:
                defval=inspected.defaults[counter]     
                if j.basetype.string.check(defval):
                    defval="'%s'"%defval
            else:
                defval=None
            counter+=1
            if param!="self":
                self.params.append(Arg(param,defval))

        if inspected.varargs!=None:
            self.params.append(Arg("*%s"%inspected.varargs,None))

        if inspected.keywords!=None:
            self.params.append(Arg("**%s"%inspected.keywords,None))

        self.comments=inspect.getdoc(method)
        if self.comments==None:
            self.comments=""        
        self.comments=j.tools.text.strip(self.comments)
        self.comments=j.tools.text.wrap(self.comments,90)

        self.linenr=inspect.getsourcelines(method)[1]
        self.name=name

        # self.methodline=inspect.getsourcelines(method)[0][0].strip().replace("self, ","").replace("self,","").replace("self","").replace(":","")

    def __str__(self):
        
        out=""
        out+="#### def %s \n\n"%(self.name)
        out+="##### arguments\n\n"
        if self.params!=[]:
            for param in self.params:
                out+=str(param)
            out+="\n"

        if self.comments!=None and self.comments.strip()!="":
            out+="##### comments\n\n"
            out+="```\n"+self.comments+"\n```\n\n"

        return out

    def __repr__(self):
        return self.__str__()


class ClassDoc():
    def __init__(self,classobj,location):
        self.location=location
        self.methods={}
        self.comments=inspect.getdoc(classobj)
        module=inspect.getmodule(classobj)
        self.path=inspect.getabsfile(module)
        self.errors=""
        self.properties=[]
        for key,val in classobj.__dict__.iteritems():
            if key.startswith("_"):
                continue
            # self.properties[key]=val
            self.properties.append(key)

    def getPath(self):
        for method in self.methods:
            return inspect.getabsfile(method)

    def addMethod(self,name,method):
        try:
            source = inspect.getsource(method)
        except:
            self.errors += '#### Error trying to add %s source in %s.\n' % (name, self.location)
        
        print "ADD METHOD:%s %s"%(self.path,name)
        md=MethodDoc(method,name,self)
        self.methods[name]=md

        return source,md.params

    def write(self,dest):
        dest2=j.system.fs.joinPaths(dest, self.location.split(".")[1],"%s.md"%self.location)
        destdir= j.system.fs.getDirName(dest2)
        j.system.fs.createDir(destdir)
        content=str(self)
        content=content.replace("\n\n\n","\n\n")
        content=content.replace("\n\n\n","\n\n")
        content=content.replace("\n\n\n","\n\n")

        #ugly temp hack, better to do with regex
        content=content.replace("\{","$%[")
        content=content.replace("\}","$%]")
        content=content.replace("{","\{")
        content=content.replace("}","\}")
        content=content.replace("$%]","\}")
        content=content.replace("$%[","\{")

        j.system.fs.writeFile(filename=dest2,contents=content)
        return dest2
        
        
    def __str__(self):
        C="<!-- toc -->\n"
        C+="## %s\n\n"%self.location
        C+="- %s\n"%self.path
        if self.properties!=[]:    
            C+="- Properties\n"    
            for prop in self.properties:
                C+="    - %s\n"%prop
        C+="\n### Methods\n"
        C+="\n"

        if self.comments!=None:
            C+="\n%s\n\n"%self.comments

        keys=self.methods.keys()
        keys.sort()
        for key in keys:
            method=self.methods[key]
            C2=str(method)
            C+=C2
            # C+=j.tools.text.prefix("    ",C2)

        
        return C
            

    def __repr__(self):
        return self.__str__()

class ObjectInspector():

    """
    functionality to inspect objectr structure and generate apifile
    """

    def __init__(self):
        # self.apiFileLocation = j.system.fs.joinPaths(j.dirs.cfgDir, "codecompletionapi", "jumpscale.api")
        # j.system.fs.createDir(j.system.fs.joinPaths(j.dirs.cfgDir, "codecompletionapi"))
        self.classDocs={}
        self.visited=[]  

    def importAllLibs(self,ignore=[],base="/opt/jumpscale7/lib/JumpScale/"):
        self.base=base
        towalk=j.system.fs.listDirsInDir(base, recursive=False, dirNameOnly=True, findDirectorySymlinks=True)        
        errors="### errors while trying to import libraries\n\n"
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

    def raiseError(self,errormsg):
        print "ERROR:%s"%errormsg
        errormsg=errormsg.strip()
        errormsg=errormsg.strip("-")
        errormsg=errormsg.strip("*")
        errormsg=errormsg.strip()
        errormsg="* %s\n"%errormsg
        j.system.fs.writeFile(filename="%s/errors.md"%self.dest,contents=errormsg,append=True)

    def generateDocs(self,dest,ignore=[]):
        self.dest=dest
        self.apiFileLocation="%s/jumpscale.api"%self.dest
        j.system.fs.writeFile("%s/errors.md"%dest,"")
        j.system.fs.createDir(self.dest)
        self.errors=self.importAllLibs(ignore=ignore)
        self.inspect()
        j.system.fs.createDir(dest)
        j.system.fs.writeFile(filename="%s/errors.md"%dest,contents=self.errors,append=True)
        self.writeDocs(dest)

    def _processMethod(self, name,method,path,classobj):
        if classobj==None:
            raise RuntimeError("cannot be None")

        classpath=".".join(path.split(".")[:-1])
        
        if classpath not in self.classDocs:
            self.classDocs[classpath]=ClassDoc(classobj,classpath)
        obj=self.classDocs[classpath]
        return obj.addMethod(name,method)

    def _processClass(self, name,path,classobj):        
        if path not in self.classDocs:
            self.classDocs[path]=ClassDoc(classobj,path)
        obj=self.classDocs[path]

    def inspect(self,objectLocationPath="j",recursive=True,parent=None,obj=None):
        """
        walk over objects in memory and create code completion api in jumpscale cfgDir under codecompletionapi
        @param object is start object
        @param objectLocationPath is full location name in object tree e.g. j.system.fs , no need to fill in
        """
        print(objectLocationPath)

        if parent==None:
            self.visited=[]

        if obj==None:
            try:
                # objectNew = eval("%s" % objectLocationPath2)
                obj= eval(objectLocationPath)
            except:                    
                self.raiseError("could not eval:%s"%objectLocationPath)
                return

        #only process our files
        try:
            if not obj.__file__.startswith(self.base):
                return
        except Exception,e:
            # print "COULD NOT DEFINE FILE OF:%s"%objectLocationPath
            pass
       

        if obj not in self.visited:
            self.visited.append(obj)
        else:
            print "RECURSIVE:%s"%objectLocationPath
            return

        attrs=dir(obj)
        try:
            for item in obj._getAttributeNames():
                if item not in attrs:
                    attrs.append(item)
        except:
            pass

        ignore=["constructor_args","NOTHING","template_class","redirect_cache"]
        def check(item):
            if item=="_getFactoryEnabledClasses":
                return True
            if item.startswith("_"):
                return False
            if item.startswith("im_"):
                return False    
            if item in ignore:
                return False
            return True
            
        attrs=[item for item in attrs if check(item)]

        for objattributename in attrs:
            objectLocationPath2 = "%s.%s" % (objectLocationPath, objattributename)

            try:
                objattribute=eval("obj.%s"%objattributename)
            except Exception,e:
                self.raiseError("cannot eval %s"%objectLocationPath2)
                continue
            
            if objattributename.upper() == objattributename:
                # is special type or constant
                print "special type: %s" % objectLocationPath2
                j.system.fs.writeFile(self.apiFileLocation, "%s?7\n" % objectLocationPath2, True)

            elif objattributename=="_getFactoryEnabledClasses":
                try:
                    for fclparent,name,obj2 in obj._getFactoryEnabledClasses():
                        if fclparent!="":
                            objectLocationPath2=objectLocationPath+"."+fclparent+"."+name
                        else:
                            objectLocationPath2=objectLocationPath+"."+name
                        self._processClass(name,objectLocationPath2,obj)
                        self.inspect(objectLocationPath=objectLocationPath2,recursive=True,parent=obj,obj=obj2)
                except Exception,e:
                    print "the _getFactoryEnabledClasses gives error"
                    import ipdb
                    ipdb.set_trace()
                    
                               
            elif str(type(objattribute)).find("'instance'") != -1 or str(type(objattribute)).find("<class") != -1 or str(type(objattribute)).find("'classobj'") != -1:
                j.system.fs.writeFile(self.apiFileLocation, "%s?8\n" % objectLocationPath2, True)
                print "class or instance: %s" % objectLocationPath2
                self.inspect(objectLocationPath2,parent=objattribute)

            elif str(type(objattribute)).find("'instancemethod'") != -1 or str(type(objattribute)).find("'function'") != -1\
                    or str(type(objattribute)).find("'staticmethod'") != -1 or str(type(objattribute)).find("'classmethod'") != -1:
                # is instancemethod
                methodpath=inspect.getabsfile(objattribute)
                if not methodpath.startswith(self.base):
                    self.classDocs.pop(objectLocationPath2,"")
                    print "SKIPPED:%s"%objectLocationPath2
                    return
                
                source, params = self._processMethod(objattributename,objattribute,objectLocationPath2,obj)
                print "instancemethod: %s" % objectLocationPath2
                j.system.fs.writeFile(self.apiFileLocation, "%s?4(%s)\n" % (objectLocationPath2, params), True)

            elif str(type(objattribute)).find("'str'") != -1 or str(type(objattribute)).find("'type'") != -1 or str(type(objattribute)).find("'list'") != -1\
                or str(type(objattribute)).find("'bool'") != -1 or str(type(objattribute)).find("'int'") != -1 or str(type(objattribute)).find("'NoneType'") != -1\
                    or str(type(objattribute)).find("'dict'") != -1 or str(type(objattribute)).find("'property'") != -1 or str(type(objattribute)).find("'tuple'") != -1:
                # is instancemethod
                print "property: %s" % objectLocationPath2
                j.system.fs.writeFile(self.apiFileLocation, "%s?8\n" % objectLocationPath2, True)

            else:
                pass
                # print((str(type(objattribute)) + " " + objectLocationPath2))

    def writeDocs(self,path):
        todelete=[]
        summary={}
        for key,doc in list(self.classDocs.items()):
            key2=".".join(key.split(".")[0:2])
            if not summary.has_key(key2):
                summary[key2]={}
            dest=doc.write(path)
            #remember gitbook info
            summary[key2][key]=j.system.fs.pathRemoveDirPart(dest,self.dest)

        summarytxt=""
        keys1=summary.keys()
        keys1.sort()
        for key1 in keys1:
            summarytxt+="* %s\n"%(key1)
            keys2=summary[key1].keys()
            keys2.sort()
            for key2 in keys2:
                summarytxt+="    * [%s](%s)\n"%(key2,summary[key1][key2])

        j.system.fs.writeFile(filename="%s/SUMMARY.md"%(self.dest),contents=summarytxt)
        

