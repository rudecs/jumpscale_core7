from JumpScale import j
import JumpScale.baselib.regextools
from .HRDBase import HRDBase

class HRDItem():
    def __init__(self,name,hrd,ttype,data,comments):
        """
        @ttype: normal,dict,list
        normal can be : int, str, float,bool
        """
        self.hrd=hrd
        self.ttype=ttype
        self.name=name
        self.data=data
        self.value=None
        self.comments=comments        

    def get(self):
        if self.value==None:
            self._process()
        return self.value

    def getAsString(self):
        data=str(self.data).strip()

        if data.lower().find("@ask")==-1 or self.data.find("$(")!=1:
            if self.value==None:
                self._process()
        else:
            return data        

        if self.value!=None:
            data=j.tools.text.pythonObjToStr(self.value)

        if self.ttype=="dict":
            data=data.strip(":")
            if data.find("\n")==-1:
                data+=":"
        if self.ttype=="list":
            data=data.strip(",")
            if data.find("\n")==-1:
                data+=","
            
        return data.strip()

    def set(self,value,persistent=True,comments=""):
        """
        @persistency always happens when format is kept
        """
        if self.hrd.prefixWithName:
            name=self.name[len(self.hrd.name)+1:]
        else:
            name=self.name
        
        self.value=value

        if comments!="":
            self.comments=comments

        self.hrd._markChanged()

        if self.hrd.keepformat:
            state="start"
            out=""
            found=False
            for line in j.system.fs.fileGetContents(self.hrd.path).split("\n"):
                if line.strip().startswith(name):                        
                    state="found"
                    continue

                if state=="found" and (len(line)==0 or line[0]==" "):
                    continue

                if state=="found":
                    state="start"
                    #now add the var
                    found=True
                    if self.comments!="":
                        out+="%s\n" % (self.comments)
                    out+="%s = %s\n" % (name, self.getAsString())

                out+="%s\n"%line

            if found==False:
                if self.comments!="":
                    out+="%s\n" % (self.comments)
                out+="%s = %s\n" % (name, self.getAsString())

            j.system.fs.writeFile(filename=self.hrd.path,contents=out)

        else:
            if persistent:
                self.hrd.save()

    def _process(self):

        #check if link to other value $(...)
        if self.data.find("$(")!=-1:
            value2=self.data
            items=j.codetools.regex.findAll(r"\$\([\w.]*\)",value2)
            if len(items)>0:
                for item in items:
                    # print "look for : %s"%item
                    item2=item.strip(" ").strip("$").strip(" ").strip("(").strip(")")

                    if self.hrd.exists(item2):
                        replacewith=j.tools.text.pythonObjToStr(self.hrd.get(item2),multiline=False)
                        value2=value2.replace(item,replacewith)
                        value2=value2.replace("//","/")
                    elif self.hrd.prefixWithName and self.hrd.tree.exists("%s.%s"%(self.hrd.name,item2)):
                        replacewith=j.tools.text.pythonObjToStr(self.hrd.get("%s.%s"%(self.hrd.name,item2)),multiline=False)
                        value2=value2.replace(item,replacewith)                    
                        value2=value2.replace("//","/")
        else:
            value2=j.tools.text.ask(self.data,self.name)
            if self.data.find("@ASK")!=-1:
                # print ("CHANGED")
                self.hrd.changed=True

        self.value=j.tools.text.hrd2machinetext(value2)
        if self.ttype=="dict":
            currentobj={}
            self.value=self.value.strip(",")
            if self.value.strip()==":":
                self.value={}
            else:
                for item in self.value.split(","):
                    key,post2=item.split(":",1)                                    
                    currentobj[key.strip()]=post2.strip()
                self.value=j.tools.text.str2var(currentobj)
        elif self.ttype=="list":
            self.value=self.value.strip(",")
            currentobj=[]
            if self.value.strip()=="":
                self.value=[]
            else:
                for item in self.value.split(","):
                    currentobj.append(item.strip())
                self.value=j.tools.text.str2var(currentobj)
        else:
            self.value=j.tools.text.str2var(self.value)

        if self.hrd.changed:
            self.hrd.save()

    def __str__(self):
        return "%-15s|%-5s|'%s' -- '%s'"%(self.name,self.ttype,self.data,self.value)

    __repr__=__str__

class HRD(HRDBase):
    def __init__(self,path=None,tree=None,content="",prefixWithName=False,keepformat=True):
        self.path=path
        if self.path is not None:
            self.name=".".join(j.system.fs.getBaseName(self.path).split(".")[:-1])
        else:
            self.name = ""
        self.tree=tree
        self.changed=False
        self.items={}
        self.commentblock=""  #at top of file
        self.keepformat=keepformat
        self.prefixWithName=prefixWithName
        self.template=""        

        if content!="":
            self.process(content)
        else:
            self.read()

    def set(self,key,value,persistent=True,comments=""):
        """
        """
        key=key.lower()
        if key not in self.items:
            self.items[key]=HRDItem(name=key,hrd=self,ttype="base",data=value,comments="")    
        self.items[key].set(value,persistent=persistent,comments=comments)

    def get(self,key,default=None,):
        key=key.lower()
        if key not in self.items:
            if default==None:
                j.events.inputerror_critical("Cannot find value with key %s in tree %s."%(key,self.path),"hrd.get.notexist")
            else:
                return default
        val= self.items[key].get()
        j.core.hrd.log("hrd get '%s':'%s'"%(key,val))
        return val

    def _markChanged(self):
        self.changed=True
        if self.tree!=None:
            self.tree.changed=True

    def save(self):
        if self.prefixWithName:
            #remove prefix from mem representation
            out=""
            l=len(self.name)+1
            for line in str(self).split("\n"):
                if line.startswith(self.name):
                    line=line[l:]
                out+="%s\n"%line
        else:
            out=str(self)

        
        j.system.fs.writeFile(self.path,out)

    def getHrd(self,key):
        #to keep common functions working
        return self

    def delete(self,key):
        if key in self.items:
            self.items.pop(key)

        out=""

        for line in j.system.fs.fileGetContents(self.path).split("\n"):
            delete=False
            line=line.strip()
            if line=="" or line[0]=="#":
                out+=line+"\n"
                continue
            if line.find("=")!=-1:
                #found line
                if line.find("#")!=-1:
                    comment=line.split("#",1)[1]
                    line2=line.split("#")[0]                    
                else:
                    line2=line
                key2,value2=line2.split("=",1)
                if key2.lower().strip()==key:
                    delete = True

            comment=""
            if delete!=True:
                out+=line+"\n"

        out = out.strip('\n') + '\n'

        j.system.fs.writeFile(self.path,out)

    def read(self):
        content=j.system.fs.fileGetContents(self.path)
        self.process(content)

    def _recognizeType(self,content):        
        content=j.tools.text.replaceQuotes(content,"something")
        if content.lower().find("@ask")!=-1:
            return "ask"
        elif content.find(":")!=-1:
            return "dict"
        elif content.find(",")!=-1:
            return "list"
        elif content.lower().strip().startswith("@ask"):
            return "ask"
        else:
            return "base"

    def applytemplate(self,path=""):
        if path=="":
            path=self.template
        if path!="":
            hrdtemplate=HRD(path=path)
            for key in list(hrdtemplate.items.keys()):
                if key not in self.items:
                    hrdtemplateitem=hrdtemplate.items[key]
                    self.set(hrdtemplateitem.name,hrdtemplateitem.data,comments=hrdtemplateitem.comments)

    def process(self,content):

        if content=="":
            content=j.system.fs.fileGetContents(self.path)        

        state="start"
        comments=""
        multiline=""
        self.content=content

        splitted=content.split("\n")
        x=-1
        go=True
        while go:
            x+=1
            if x==len(splitted):
                go=False
                continue
            line=splitted[x]
            line2=line.strip()

            if len(line)>0 and line.find("#")!=-1:
                line,comment0=line.split("#",1)
                line2=line.strip()
                comments+="#%s\n"%comment0
            
            if line2=="":
                if state=="multiline":
                    #end of multiline var needs to be processed
                    state="var"
                else:
                    continue

            if line2.startswith("@"):
                continue

            if state=="multiline":
                if line[0]!=" ":
                    #if post was empty then we need to process current line again
                    if post.strip()=="":
                        x=x-1
                    #end of multiline var needs to be processed
                    state="var"

            #look for comments at start of content
            if state=="start":
                if line[0]=="#":
                    self.commentblock+="%s\n"%line
                    continue
                else:
                    state="look4var"

            if state=="look4var":
                # print ("%s:%s"%(state,line))

                if line.find("=")!=-1:
                    pre,post=line2.split("=",1)                        
                    vartype="unknown"
                    name=pre.strip()
                    if post.strip()=="" or post.strip().lower()=="@ask,":
                        state="multiline"
                        if  post.lower().strip().startswith("@ask"):
                            vartype="ask"                            
                        post=post.strip()+" " #make sure there is space trailing
                        continue
                    else:
                        vartype=self._recognizeType(post)
                        post=post.strip(",").strip(":")
                        # print "%s vartype:%s"%(line,vartype)
                        post=post.strip()
                        state="var"

                if line[0]=="#":
                    comments+="%s\n"%line

            if state=="multiline":                             
                if vartype=="unknown":
                    #means first line of multiline, this will define type
                    if line2.find(":")!=-1 and line2[-1]==",":
                        vartype="dict"
                    elif line2[-1]==",":
                        vartype="list"
                    else:
                        vartype="base" #newline text

                if vartype=="unknown":
                    raise RuntimeError("parse error, only dict, list, normal or ask format in multiline")

                if vartype=="base":
                    post+="%s\\n"%line2
                elif vartype=="dict" or vartype=="list":
                    post+="%s "%line2
                elif vartype=="ask":
                    post+="%s "%line2

            if state=="var":
                #now we have 1 liners and we know type
                if vartype=="ask":
                    vartype="base" #ask was temporary type, is really a string
                
                if self.prefixWithName:
                    name="%s.%s"%(self.name,name)
                self.items[name]=HRDItem(name,self,vartype,post,comments)
                if self.tree!=None:
                    self.tree.items[name]=self.items[name]
                    
                state="look4var"
                comments=""
                vartype="unknown"

        self.applytemplate()

