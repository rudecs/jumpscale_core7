from JumpScale import j
import JumpScale.baselib.regextools
from .HRDBase import HRDBase
import binascii
import copy

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
        self.temp=False   

    def get(self):
        if self.ttype=="binary":
            return self.data
        if self.value==None:
            self._process()
        return self.value

    def getAsString(self):
        if self.ttype=="binary":
            return self.data

        if self.value==None:
            data=str(self.data).strip()
            self._process()
        # elif data.lower().find("@ask")!=-1 or self.data.find("$(")!=1 and :
        #     self._process()

        data=j.tools.text.pythonObjToStr(self.value)
        if not (self.ttype=="dict" or self.ttype=="list"):
            # print "'%s'"%data
            if data.find("\n   ")!=0:
                data=data.strip()
        else:
            data=data.strip("\n")
            
        return data


    def set(self,value,persistent=True,comments="",temp=False):
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

        if temp:
            self.temp=True
            return
        
        self.hrd._markChanged()

        # if self.hrd.keepformat and persistent:
        #     state="start"
        #     out=""
        #     found=False
        #     for line in j.system.fs.fileGetContents(self.hrd.path).split("\n"):
        #         if line.strip().startswith(name):                        
        #             state="found"
        #             continue

        #         if state=="found" and (len(line)==0 or line[0]==" "):
        #             continue

        #         if state=="found":
        #             state="start"
        #             #now add the var
        #             found=True
        #             if self.comments!="":
        #                 out+="%s\n" % (self.comments)
        #             out+="%s = %s\n" % (name, self.getAsString())

        #         out+="%s\n"%line

        #     if found==False:
        #         if self.comments!="":
        #             out+="%s\n" % (self.comments)
        #         out+="%s = %s\n" % (name, self.getAsString())

        #     j.system.fs.writeFile(filename=self.hrd.path,contents=out)

        if persistent:
            self.hrd.save()

    def _process(self):
        data=copy.copy(self.data)
        #check if link to other value $(...)
        if data.find("$(")!=-1:
            items=j.codetools.regex.findAll(r"\$\([\w.]*\)",data)
            if len(items)>0:
                for item in items:
                    partial = True
                    if item == data:
                        partial = False
                    # print "look for : %s"%item
                    item2=item.strip(" ").strip("$").strip(" ").strip("(").strip(")")
                    if self.hrd.exists(item2):
                        replacewith = j.tools.text.pythonObjToStr(self.hrd.get(item2), multiline=False, partial=partial)
                        data=data.replace(item,replacewith)                            
                        # data=data.replace("//","/")
                    elif self.hrd.prefixWithName and self.hrd.tree!=None and self.hrd.tree.exists("%s.%s"%(self.hrd.name,item2)):
                        replacewith = j.tools.text.pythonObjToStr(self.hrd.get("%s.%s" % (self.hrd.name,item2)), multiline=False, partial=partial)
                        data=data.replace(item,replacewith)                    
                        # data=data.replace("//","/")

        data=j.tools.text.dealWithList(data)

        if data.find("@ASK")!=-1:
            # print ("%s CHANGED"%self)
            self.hrd.changed=True        

        ttype, data=j.tools.text.ask(data,self.name,args=self.hrd.args)
        self.data = data
        if self.ttype == "base" and ttype:
            self.ttype = ttype

        if self.ttype=="str" or self.ttype=="base":
            self.value=data.strip().strip("'")
            self.value=j.tools.text.machinetext2val(self.value)

        elif self.ttype=="dict":
            currentobj={}
            self.value=data.strip(",")
            if self.value.strip()==":":
                self.value={}
            else:
                for item in self.value.split(","):
                    item = item.strip()
                    if item == "":
                        continue
                    if item.find(":") == -1:
                        j.events.inputerror_critical("In %s/%s: cannot parse:'%s', need to find : to parse dict"%(self.hrd.name,self.name,item))
                    key,post2=item.split(":",1)
                    currentobj[key.strip()]=j.tools.text.machinetext2val(post2.strip())
                self.value=currentobj

        elif self.ttype=="list":
            self.value=data.strip(",")
            currentobj=[]
            if self.value.strip()=="":
                self.value=[]
            else:
                for item in self.value.split(","):
                    if item.strip()=="":
                        continue
                    currentobj.append(j.tools.text.machinetext2val(item.strip()))
                self.value=currentobj

        elif self.ttype=="binary":
            self.value="BINARY"

        else:
            self.value=j.tools.text.str2var(data)

        if self.hrd.changed:
            # print "SAVE"
            self.hrd.save()
            self.hrd.changed=False

    def __str__(self):
        if self.ttype!="binary":
            return "%-15s|%-5s|'%s' -- '%s'"%(self.name,self.ttype,self.data,self.value)
        else:
            return "%-15s|%-5s|'%s' -- '%s'"%(self.name,self.ttype,"BINARY",self.value)

    __repr__=__str__

class HRD(HRDBase):
    def __init__(self,path=None,tree=None,content="",prefixWithName=False,keepformat=True,args={},templates=[],istemplate=False):
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
        self.templates=templates    
        self.args=args   
        self.istemplate=istemplate

        if content!="":
            self.process(content)
        else:
            self.read()

    def set(self,key,value="",persistent=True,comments="",temp=False,ttype=None,data=""):
        """
        """
        key=key.lower()
        if key not in self.items:
            self.items[key]=HRDItem(name=key,hrd=self,ttype=ttype,data=value,comments="")
        if data!="":
            self.items[key].data=data
        else:
            self.items[key].set(value,persistent=persistent,comments=comments,temp=temp)

    def get(self,key,default=None,):
        key=key.lower()
        if key not in self.items:
            if default==None:
                j.events.inputerror_critical("Cannot find value with key %s in tree %s."%(key,self.path),"hrd.get.notexist")
            else:
                return default
        val= self.items[key].get()
        val = val.strip() if isinstance(val, basestring) else val
        j.core.hrd.log("hrd get '%s':'%s'"%(key,val))
        return val

    def _markChanged(self):
        self.changed=True
        if self.tree!=None:
            self.tree.changed=True

    def save(self):
        if self.istemplate:
            raise RuntimeError("should not save template")
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
        if not j.system.fs.exists(path=self.path):
            j.do.writeFile(self.path,"")
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

    def applyTemplates(self,path="",hrd=None):

        if self.istemplate:
            return

        templates=[]
        if hrd!=None:
            hrd.istemplate=True
            templates=[hrd]
        elif path!="":
            templates=[HRD(path=path,istemplate=True)]
            
        for path in self.templates:
            templates.append(HRD(path=path,istemplate=True))

        change=False
        for hrdtemplate in templates:

            for key in list(hrdtemplate.items.keys()):
                if key in self.args:
                    #means key does already exist in HRD arguments, will use that value
                    hrdtemplateitem=hrdtemplate.items[key]
                    self.set(hrdtemplateitem.name,self.args[key],comments=hrdtemplateitem.comments,persistent=False,ttype=hrdtemplateitem.ttype)
                    continue                    
                elif key not in self.items:
                    #its not in hrd yet
                    change=True
                    hrdtemplateitem=hrdtemplate.items[key]
                    if hrdtemplateitem.data.find("@ASK")!=-1:
                        ttype, val=j.tools.text.ask(hrdtemplateitem.data,name=key,args=self.args)
                        if not ttype:
                            ttype = hrdtemplateitem.ttype
                        self.set(hrdtemplateitem.name,val,comments=hrdtemplateitem.comments,persistent=False,ttype=ttype)
                    else:
                        self.set(hrdtemplateitem.name,hrdtemplateitem.get(),comments=hrdtemplateitem.comments,persistent=False,ttype=ttype)
        

        for key in self.args:
            self.set(key,self.args[key])

        if templates<>[]:
            if change:
                self.save()


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
        vartype="unknown"
        while go:
            x+=1
            if x==len(splitted):
                go=False
                continue
            line=splitted[x]

            # print ("%s:%s:%s"%(state,vartype,line))
            
            if not vartype.startswith("binary"): 
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
            else:
                line2=line

            if state=="multiline":

                if vartype.startswith("binary"):
                    if line2.startswith("#BINARYEND#########"):
                        #found end of binary block
                        post=post[:-1]
                        state="var"
                elif line[0]!=" ":
                    #if post was empty then we need to process current line again
                    if post.strip()=="":
                        x=x-1
                    #end of multiline var needs to be processed
                    state="var"
                    # print ("varnew:%s"%(line))

            #look for comments at start of content
            if state=="start":
                if line[0]=="#":
                    self.commentblock+="%s\n"%line
                    continue
                else:
                    state="look4var"

            if state=="look4var":
                # print ("%s:%s:%s"%(state,vartype,line))

                if line.find("=")!=-1:
                    pre,post=line2.split("=",1)                        
                    vartype="unknown"
                    name=pre.strip()
                    if post.strip()=="" or post.strip().startswith("b") or post.strip().lower()=="@ask,":
                        state="multiline"
                        # print ("multilinenew:%s"%(line))
                        if  post.lower().strip().startswith("@ask"):
                            vartype="ask"
                            post=post.strip()+" " #make sure there is space trailing
                        elif post.strip()=="b":
                            post=""
                            vartype="binary"
                        elif post.strip()=="bqp":
                            post=""
                            vartype="binaryqp"                            
                        else:
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
                    line2=j.tools.text.hrd2machinetext(line2)
                    if line2.find(":")!=-1 and line2[-1]==",":
                        vartype="dict"
                    elif line2[-1]==",":
                        vartype="list"
                    else:
                        vartype="base" #newline text                

                if vartype=="unknown":
                    raise RuntimeError("parse error, only dict, list, normal or ask format in multiline")

                if vartype=="base":
                    line2=j.tools.text.hrd2machinetext(line2,onlyone=True)  
                    post+="%s\\n"%line2
                elif vartype.startswith("binary"):
                    post+="%s\n"%line2                    
                elif vartype=="dict" or vartype=="list":
                    line2=j.tools.text.hrd2machinetext(line2)
                    post+="%s "%line2
                elif vartype=="ask":
                    line2=j.tools.text.hrd2machinetext(line2)
                    post+="%s "%line2

                # print ("%s:%s:%s"%(state,vartype,line2))

            if state=="var":
                #now we have 1 liners and we know type
                # print ("%s:%s"%(state,line))
                if vartype=="ask":
                    vartype="base" #ask was temporary type, is really a string

                name2 = name
                if self.prefixWithName:
                    name2="%s.%s"%(self.name,name)

                if vartype=="binaryqp":
                    post=binascii.a2b_qp(post)
                    vartype="binary"

                self.items[name]=HRDItem(name,self,vartype,post,comments)
                if self.tree!=None:
                    self.tree.items[name2]=self.items[name]
                    
                state="look4var"
                comments=""
                vartype="unknown"

        self.applyTemplates()

