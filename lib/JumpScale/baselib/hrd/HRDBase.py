from JumpScale import j
import binascii
import copy
from collections import OrderedDict
class HRDBase():

    def prefix(self, key,depth=0):
        """
        @param depth means prefix level to return
        """
        result=[]
        for knownkey in list(self.items.keys()):
            # print "prefix: %s - %s"%(knownkey,key)
            if knownkey.startswith(key):
                if depth>0:                    
                    knownkey=".".join(knownkey.split(".")[0:depth])
                if knownkey not in result:                    
                    result.append(knownkey)

        def sorter(key):
            parts = key.split('.')
            if parts[-1].isdigit():
                return int(parts[-1])
            return key

        result.sort(key=sorter)
        return result

    def prefixexists(self,key):
        result=[]
        for knownkey in list(self.items.keys()):
            # print "prefix: %s - %s"%(knownkey,key)
            if knownkey.startswith(key):
                return True


    def getBool(self,key,default=None):
        res=self.get(key,default=default)
        if res==None:
            return False
        res2=str(res)
        if res==True or res2=="1" or res2.lower()=="true":
            return True
        else:
            return False            

    def getInt(self,key,default=None):
        if default!=None:
            default=int(default)        
        res=self.get(key,default=default)
        return j.tools.text.getInt(res)

    def getStr(self,key,default=None):
        if default!=None:
            default=str(default)        
        res=self.get(key,default=default)
        res=j.tools.text.pythonObjToStr(res,multiline=False, canBeDict=False)
        res=res.strip()
        return res

    def listAdd(self,key,item):
        arg=self.get(key)
        if item not in arg:
            arg.append(item)
        self.set(key,arg)

    def getFloat(self,key):
        res=self.get(key)
        return j.tools.text.getFloat(res)

    def exists(self,key):
        return key in self.items

    def getList(self,key):
        lst=self.get(key)
        if j.basetype.list.check(lst):
            return lst
        lst=str(lst)
        if j.basetype.string.check(lst):
            items=[item.strip() for item in lst.split(",")]        
            items=[item for item in items if item!=""]
            return items
        raise RuntimeError("no list for %s"%key)

    def getDict(self,key):
        ddict=self.get(key)
        if j.basetype.dictionary.check(ddict):
            for key,item in ddict.items():
                ddict[key]=j.tools.text.str2var(item)
            return ddict
        if ddict.strip()=="":
            return OrderedDict()   
        raise RuntimeError("no dict for %s"%key)

    def getListFromPrefix(self, prefix):
        """
        returns values from prefix return as list
        """
        result=[]
        for key in self.prefix(prefix):
            result.append(self.get(key))
        return result
  
    def getDictFromPrefix(self, prefix):
        """
        returns values from prefix return as list
        """
        result = OrderedDict()
        l=len(prefix)
        for key in self.prefix(prefix):
            if prefix!="":
                key2=key[l+1:]
            else:
                key2=key
            result[key2]=self.get(key)
        return result

    def getHRDAsDict(self):
        ddict=self.getDictFromPrefix("")
        keys=ddict.keys()
        keys.sort()
        prevkey=""
        for key in keys:
            if key.count(".")==1:
                keyparts=key.split(".")
                if j.tools.text.isNumeric(keyparts[1]):
                    if keyparts[0] not in ddict.keys():
                        ddict[keyparts[0]]=[]
                    ddict[keyparts[0]].append(self.get(key).replace("\\n","\n"))
                    ddict.pop(key)                
            elif key.count(".")==2:
                keyparts=key.split(".")
                if j.tools.text.isNumeric(keyparts[1]):
                    if keyparts[0] not in ddict.keys():
                        ddict[keyparts[0]]=[]
                    newkey="%s_%s"%(keyparts[0],keyparts[1])
                    if newkey!=prevkey:
                        ddict[keyparts[0]].append(OrderedDict())
                    # print "%s %s"%(prevkey,newkey)
                    prevkey=newkey
                    ddict[keyparts[0]][-1][keyparts[2]]=self.get(key).replace("\\n","\n")
                    ddict.pop(key)                
        return ddict

    def getListFromPrefixEachItemDict(self, prefix,musthave=[],defaults=OrderedDict(),aredict=OrderedDict(),arelist=[],areint=[],arebool=[]):
        """
        returns values from prefix return as list
        each value represents a dict
        @param musthave means for each item which is dict, we need to have following keys
        @param specifies the defaults
        @param aredicts & arelist specifies which types
        """
        result=[]
        for key in self.prefix(prefix):
            result.append(copy.copy(self.get(key)))

        def processdict(ddict,musthave=[],defaults=OrderedDict(),aredicts=OrderedDict(),arelist=[],arebool=[]):
            # print "##\n%s\n##\n"%ddict
            for key in musthave:
                if key not in ddict.keys():
                    ddict[key]=""

            for key in ddict.keys():

                if key in defaults:
                    if ddict[key]=="":
                        ddict[key]=defaults[key]

                #no default            
                if key in areint:
                    ddict[key]=str(ddict[key]).strip().strip(",")
                    if ddict[key]=="":
                        ddict[key]=0
                    else:
                        ddict[key]=j.tools.text.getInt(ddict[key])
                
                elif key in arebool:
                    ddict[key]=str(ddict[key]).strip().strip(",")
                    if ddict[key]=="":
                        ddict[key]=False
                    else:
                        ddict[key]=j.tools.text.getBool(ddict[key])                        
                
                elif key in aredict:
                    checkval=str(ddict[key]).strip().strip(",")
                    if checkval=="":
                        ddict[key]=OrderedDict()
                    elif j.basetype.dictionary.check(ddict[key]):
                        for key3,val3 in ddict[key].items():
                            ddict[key][key3]=j.tools.text.machinetext2val(str(ddict[key][key3]))
                    else:
                        # ddict[key]=j.tools.text.machinetext2val(ddict[key])
                        ddict[key]=j.tools.text.getDict(checkval)                            
                        for key3,val3 in ddict[key].items():
                            ddict[key][key3]=j.tools.text.str2var(str(ddict[key][key3]))
                
                elif key in arelist:
                    checkval=str(ddict[key]).strip().strip(",")
                    if checkval=="":
                        ddict[key]=[]
                    elif j.basetype.list.check(ddict[key]):
                        for val3 in ddict[key]:
                            val3=j.tools.text.machinetext2val(str(val3))
                    else:
                        # ddict[key]=j.tools.text.machinetext2val(str(ddict[key]))
                        ddict[key]=j.tools.text.getList(checkval)
                        ddict[key]=[j.tools.text.str2var(item) for item in ddict[key]]

                else:
                    ddict[key]=j.tools.text.machinetext2val(str(ddict[key]))

            return ddict

        for item in result:
            item=processdict(item,musthave,defaults,aredict,arelist,arebool)

        return result   

    def checkValidity(self,template,hrddata=OrderedDict()):
        """
        @param template is example hrd content block, which will be used to check against, 
        if params not found will be added to existing hrd 
        """      
        from .HRD import HRD
        hrdtemplate=HRD(content=template)
        for key in list(hrdtemplate.items.keys()):
            if key not in self.items:
                hrdtemplateitem=hrdtemplate.items[key]
                if key in hrddata:
                    data=hrddata[key]
                else:
                    data=hrdtemplateitem.data
                self.set(hrdtemplateitem.name,data,comments=hrdtemplateitem.comments)

    def processall(self):
        for key,hrditem in list(self.items.items()):
            hrditem._process()

    def pop(self,key):
        if key in self.items:
            self.items.pop(key)

    def applyOnDir(self,path,filter=None, minmtime=None, maxmtime=None, depth=None,changeFileName=True,changeContent=True,additionalArgs=OrderedDict()):
        """
        look for $(name) and replace with hrd value
        """
        j.core.hrd.log("hrd %s apply on dir:%s"%(self.name,path),category="apply")
        
        items=j.system.fs.listFilesInDir( path, recursive=True, filter=filter, minmtime=minmtime, maxmtime=maxmtime, depth=depth)
        for item in items:
            if changeFileName:
                item2=self._replaceVarsInText(item,additionalArgs=additionalArgs)
                if item2!=item:
                     j.system.fs.renameFile(item,item2)
                    
            if changeContent:
                self.applyOnFile(item2,additionalArgs=additionalArgs)

    def applyOnFile(self,path,additionalArgs=OrderedDict()):
        """
        look for $(name) and replace with hrd value
        """

        j.core.hrd.log("hrd:%s apply on file:%s"%(self.path,path),category="apply")
        content=j.system.fs.fileGetContents(path)
        content=self._replaceVarsInText(content,additionalArgs=additionalArgs)
        j.system.fs.writeFile(path,content)

    def applyOnContent(self,content,additionalArgs=OrderedDict()):
        """
        look for $(name) and replace with hrd value
        """

        content=self._replaceVarsInText(content,additionalArgs=additionalArgs)
        return content

    def _replaceVarsInText(self,content,additionalArgs=OrderedDict()):
        if content=="":
            return content
            
        items=j.codetools.regex.findAll(r"\$\([\w.]*\)",content)
        j.core.hrd.log("replace vars in hrd:%s"%self.path,"replacevar",7)
        if len(items)>0:
            for item in items:
                # print "look for : %s"%item
                item2=item.strip(" ").strip("$").strip(" ").strip("(").strip(")")

                if item2.lower() in additionalArgs:
                    newcontent=additionalArgs[item2.lower()]
                    newcontent=str(newcontent)
                    content=content.replace(item,newcontent)
                else:
                    if self.exists(item2):
                        replacewith=j.tools.text.pythonObjToStr(self.get(item2),multiline=True).strip("'")
                        content=content.replace(item,replacewith)            
        return content          

    def __repr__(self):

        parts=[]
        keys=list(self.items.keys())
        keys.sort()
        if self.commentblock!="":
            out=[self.commentblock]
        else:
            out=[""]
        keylast=[]

        for key in keys:
            keynew=key.split(".")
            
            hrditem=self.items[key]   
            if hrditem.temp:
                continue

            if hrditem.comments!="":
                out.append("")
                out.append("%s" % (hrditem.comments.strip()))
            else:
                if keylast!=[] and keynew[0]!=keylast[0]:
                    if out[-1]<>"":
                        out.append("")

            if not isinstance( hrditem.data,str):
                #@todo fix this bug
                # raise RuntimeError("BUG SHOULD ALWAYS BE STR")
                pass

                
            if isinstance( hrditem.data,str) and hrditem.data.find("@ASK")!=-1:
                val=hrditem.value
                out.append("%-30s = %s" % (key, val))
            elif hrditem.ttype =="string":                
                val=hrditem.getAsString()
                if val.find("\n")!=-1:
                    out.append("%-30s = '%s'" % (key, val.strip("'")))
                else:
                    out.append("%-30s = %s" % (key, val))

            elif hrditem.ttype =="list" or hrditem.ttype =="dict":
                val=hrditem.getAsString()                
                out.append("%-30s =\n%s" % (key, val))
                out.append("")

            elif hrditem.ttype !="binary":
                val=hrditem.getAsString()
                out.append("%-30s = %s" % (key, val))                
            else:
                out.append("%-30s = bqp\n%s\n#BINARYEND#########\n\n"%(key,binascii.b2a_qp(hrditem.data)))
            # print("%s'''%s'''"%(hrditem.ttype,val))
            keylast=key.split(".")
        out=out[1:]
        out="\n".join(out).replace("\n\n\n","\n\n")
        return out

    def __str__(self):
        return self.__repr__()

