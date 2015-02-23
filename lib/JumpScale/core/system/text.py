import time
from JumpScale import j
import re
matchquote = re.compile(r'\'[^\']*\'')
matchlist = re.compile(r'\[[^\']*\]')
re_nondigit= re.compile(r'\D')
re_float = re.compile(r'[0-9]*\.[0-9]+')
re_digit = re.compile(r'[0-9]*')
import unicodedata

class Text:
    @staticmethod
    def toStr(value, codec='utf-8'):
        if isinstance(value, unicode):
            value=unicodedata.normalize('NFKD',value)
            value = value.encode(codec)
        return bytes(value)

    @staticmethod
    def toAscii(value,maxlen=0):
        value=value.encode('ascii','ignore')
        # out=""
        # for item in value:
        #     if ord(item)>255:
        #         continue
        #     out+=item
        if maxlen>0 and len(out)>maxlen:
            out=out[0:maxlen]
        out=out.replace("\r","")        
        return out

    @staticmethod
    def toUnicode(value, codec='utf-8'):
        if isinstance(value, str):
            return value.decode(codec)
        elif isinstance(value, str):
            return value
        else:
            return str(value)

    @staticmethod
    def prefix(prefix,txt):
        out=""
        txt=txt.rstrip("\n")
        for line in txt.split("\n"):
            out+="%s%s\n"%(prefix,line)
        return out

    @staticmethod
    def prefix_remove(prefix,txt,onlyPrefix=False):
        """
        @param onlyPrefix if True means only when prefix found will be returned, rest discarded
        """
        out=""
        txt=txt.rstrip("\n")
        l=len(prefix)
        for line in txt.split("\n"):
            if line.find(prefix)==0:
                out+="%s\n"%(line[l:])
            elif onlyPrefix==False:
                out+="%s\n"%(line)
        return out

    @staticmethod
    def prefix_remove_withtrailing(prefix,txt,onlyPrefix=False):
        """
        there can be chars for prefix (e.g. '< :*: aline'  and this function looking for :*: would still work and ignore '< ')
        @param onlyPrefix if True means only when prefix found will be returned, rest discarded
        """
        out=""
        txt=txt.rstrip("\n")
        l=len(prefix)
        for line in txt.split("\n"):
            if line.find(prefix)>-1:
                out+="%s\n"%(line.split(prefix,1)[1])
            elif onlyPrefix==False:
                out+="%s\n"%(line)        
        return out

    @staticmethod
    def addCmd(out,entity,cmd):
        out+="!%s.%s\n"%(entity,cmd)
        return out

    @staticmethod
    def addTimeHR(line,epoch,start=50):
        if int(epoch)==0:
            return line
        while len(line)<start:
            line+=" "
        line+="# "+time.strftime('%Y/%m/%d %H:%M:%S',time.localtime(int(epoch)))
        return line

    @staticmethod
    def addVal(out,name,val,addtimehr=False):            
        if isinstance( val, int ):
            val=str(val)
        while len(val)>0 and val[-1]=="\n":
            val=val[:-1]
        if len(val.split("\n"))>1:
            out+="%s=...\n"%(name)
            for item in val.split("\n"):
                out+="%s\n"%(item)
            out+="...\n"
        else:
            line="%s=%s"%(name,val)
            if addtimehr:
                line=Text.addTimeHR(line,val)
            out+="%s\n"%line
        return out

    @staticmethod
    def isNumeric(txt):        
        return re_nondigit.search(txt)==None

    @staticmethod
    def ask(content,name=None,args={}):
        """
        look for @ASK statements in text, where found replace with input from user

        syntax for ask is:
            @ASK name:aname type:str descr:adescr default:adefault regex:aregex retry:10 minValue:10 maxValue:20 dropdownvals:1,2,3

            descr, default & regex can be between '' if spaces inside

            types are: str,float,int,bool,dropdown,multiline
            the multiline will open joe as editor

            retry means will keep on retrying x times until ask is done properly

            dropdownvals is comma separated list of values to ask for when type dropdown

        @ASK can be at any position in the text

        """        
        content=Text.eval(content)
        if content.strip()=="":
            return None, content

        endlf=content[-1]=="\n"
        ttype = None
        
        out=""
        for line in content.split("\n"):

            # print ("ask:%s"%line)

            if line.find("@ASK")==-1:
                out+="%s\n"%line
                continue

            result="ERROR:UNKNOWN VAL FROM ASK"

            prefix,end=line.split("@ASK",1)
            tags=j.core.tags.getObject(end.strip())

            if tags.tagExists("name"):
                name=tags.tagGet("name")
            else:
                if name==None:
                    if line.find("=")!=-1:
                        name=line.split("=")[0].strip()
                    else:
                        name=""
            
            if name in args:
                result=args[name]
                out+="%s%s\n"%(prefix,result)
                continue
            
            if name in args:
                result=args[name]
                out+="%s%s\n"%(prefix,result)
                continue

            if tags.tagExists("type"):
                ttype=tags.tagGet("type").strip().lower()
                if ttype=="string":
                    ttype="str"
            else:
                ttype="str"
            if tags.tagExists("descr"):
                descr=tags.tagGet("descr")
            else:
                if name!="":
                    descr="Please provide value for %s of type %s"% (name, ttype)
                else:
                    descr="Please provide value"

            # name=name.replace("__"," ")

            descr=descr.replace("__"," ")
            descr=descr.replace("\\n","\n")

            if tags.tagExists("default"):
                default=tags.tagGet("default")
            else:
                default=""

            if tags.tagExists("retry"):
                retry = int(tags.tagGet("retry"))
            else:
                retry = -1

            if tags.tagExists("regex"):
                regex = tags.tagGet("regex")
            else:
                regex = None

            if len(descr)>30 and ttype not in ('dict', 'multiline'):
                print (descr)
                descr=""

            # print "type:'%s'"%ttype
            if ttype=="str":
                result=j.console.askString(question=descr, defaultparam=default, regex=regex, retry=retry)

            elif ttype=="list":
                result=j.console.askString(question=descr, defaultparam=default, regex=regex, retry=retry)

            elif ttype=="multiline":
                result=j.console.askMultiline(question=descr)

            elif ttype=="float":
                result=j.console.askString(question=descr, defaultparam=default, regex=None)
                #check getFloat
                try:
                    result=float(result)
                except:
                    j.events.inputerror_critical("Please provide float.","system.text.ask.neededfloat")
                result=str(result)
            
            elif ttype=="int":
                if tags.tagExists("minValue"):
                    minValue = int(tags.tagGet("minValue"))
                else:
                    minValue = None

                if tags.tagExists("maxValue"):
                    maxValue = int(tags.tagGet("maxValue"))
                else:
                    maxValue = None

                if not default:
                    default=None
                result=j.console.askInteger(question=descr,  defaultValue=default, minValue=minValue, maxValue=maxValue, retry=retry)

            elif ttype=="bool":
                if descr!="":
                    print(descr)
                result=j.console.askYesNo()
                if result:
                    result=1
                else:
                    result=0

            elif ttype=="dropdown":
                if tags.tagExists("dropdownvals"):
                    dropdownvals=tags.tagGet("dropdownvals")
                else:
                    j.events.inputerror_critical("When type is dropdown in ask, then dropdownvals needs to be specified as well.")
                choicearray=[item.strip() for item in dropdownvals.split(",")]
                result=j.console.askChoice(choicearray, descr=descr, sort=True)
            elif ttype == 'dict':
                rawresult = j.console.askMultiline(question=descr)
                result = "\n"
                for line in rawresult.splitlines():
                    result += "    %s,\n" % line.strip().strip(',')

            else:
                j.events.inputerror_critical("Input type:%s is invalid (only: bool,int,str,string,dropdown,list,dict,float)"%ttype)            

            out+="%s%s\n"%(prefix,result)

        # if endlf==False:
        out=out[:-1]
        return ttype, out

    @staticmethod
    def getMacroCandidates( txt):
        """
        look for {{}} return as list
        """
        result = []
        items = txt.split("{{")
        for item in items:
            if item.find("}}") != -1:
                item = item.split("}}")[0]
                if item not in result:
                    result.append("{{%s}}" % item)
        return result

    @staticmethod
    def _str2var(string):
        """
        try to check int or float or bool
        """
        if string.lower()=="empty":
            return "n",None
        if string.lower()=="none":
            return "n",None
        if string=="":
            return "s",""
        string2=string.strip()
        if string2.lower()=="true":
            return "b",True
        if string2.lower()=="false":
            return "b",False
        #check int
        if re_nondigit.search(string2)==None and string2!="":
            # print "int:'%s'"%string2
            return "i",int(string2)
        #check float
        match=re_float.search(string2)
        if match!=None and match.start()==0 and match.end()==len(string2):
            return "f",float(string2)

        return "s",Text.machinetext2str(string)

    @staticmethod
    def str2var(string):
        """
        convert list, dict of strings 
        or convert 1 string to python objects
        """
        try:
            if j.basetype.list.check(string):
                ttypes=[]
                for item in string:
                    ttype,val=Text._str2var(item)
                    if ttype not in ttypes:
                        ttypes.append(ttype)
                if "s" in ttypes:
                    result=[str(Text.machinetext2val(item))  for item in string]
                elif "f" in ttypes and "b" not in ttypes:
                    result=[Text.getFloat(item) for item in string]
                elif "i" in ttypes and "b" not in ttypes:
                    result=[Text.getInt(item) for item in string]
                elif "b" == ttypes:
                    result=[Text.getBool(item) for item in string]                
                else:
                    result=[str(Text.machinetext2val(item)) for item in string]
            elif j.basetype.dictionary.check(string):
                ttypes=[]
                result={}
                for key,item in list(string.items()):
                    ttype,val=Text._str2var(item)
                    if ttype not in ttypes:
                        ttypes.append(ttype)
                if "s" in ttypes:                        
                    for key,item in list(string.items()):
                        result[key]=str(Text.machinetext2val(item)) 
                elif "f" in ttypes and "b" not in ttypes:
                    for key,item in list(string.items()):
                        result[key]=Text.getFloat(item)
                elif "i" in ttypes and "b" not in ttypes:
                    for key,item in list(string.items()):
                        result[key]=Text.getInt(item)
                elif "b" == ttypes:
                    for key,item in list(string.items()):
                        result[key]=Text.getBool(item)
                else:
                    for key,item in list(string.items()):
                        result[key]=str(Text.machinetext2val(item)) 
            elif isinstance(string,str) or isinstance(string,float) or isinstance(string,int):
                ttype,result=Text._str2var(str(string))
            else:
                j.events.inputerror_critical("Could not convert '%s' to basetype, input was no string, dict or list."%(string),"text.str2var")    
            return result
        except Exception as e:
            j.events.inputerror_critical("Could not convert '%s' to basetype, error was %s"%(string,e),"text.str2var")

            
    @staticmethod
    def eval(code):
        """
        look for {{}} in code and evaluate as python result is converted back to str
        """
        candidates=Text.getMacroCandidates(code)
        for itemfull in candidates:
            item=itemfull.strip("{{").strip("}}")
            try:
                result=eval(item)
            except Exception as e:
                raise RuntimeError("Could not execute code in j.tools.text,%s\n%s,Error was:%s"%(item,code,e))
            result=Text.pythonObjToStr(result,multiline=False).strip()
            code=code.replace(itemfull,result)
        return code        


    @staticmethod
    def pythonObjToStr1line(obj):
        return Text.pythonObjToStr(obj,False,canBeDict=False)

    @staticmethod
    def pythonObjToStr(obj,multiline=True,canBeDict=True,partial=False):
        """
        try to convert a python object to string representation works for None, bool, integer, float, dict, list
        """
        if obj==None:
            return ""
        elif isinstance(obj,unicode):
            obj=obj.decode("utf8")
            return obj
        elif j.basetype.boolean.check(obj):
            if obj==True:
                obj="True"
            else:
                obj="False"
            return obj
        elif j.basetype.string.check(obj):
            isdict = canBeDict and obj.find(":")!=-1
            if obj.strip()=="":
                return ""
            if obj.find("\n")!=-1 and multiline:
                obj="\n%s"%Text.prefix("    ",obj.strip())
            elif not isdict or obj.find(" ")!=-1 or obj.find("/")!=-1 or obj.find(",")!=-1:
                if not partial:
                    obj="'%s'"%obj.strip("'")
                else:
                    obj="%s"%obj.strip("'")
            return obj
        elif j.basetype.integer.check(obj) or j.basetype.float.check(obj):
            return str(obj)
        elif j.basetype.list.check(obj):
            # if not canBeDict:
            #     raise RuntimeError("subitem cannot be list or dict for:%s"%obj)
            if multiline:
                resout="\n"
                for item in obj:
                    resout+="    %s,\n"%Text.pythonObjToStr1line(item)
                resout=resout.rstrip().strip(",")+",\n"
            else:
                resout='['
                for item in obj:
                    resout+="%s,"%Text.pythonObjToStr1line(item)
                resout=resout.rstrip().strip(",")+"]"

            return resout

        elif j.basetype.dictionary.check(obj):
            if not canBeDict:
                raise RuntimeError("subitem cannot be list or dict for:%s"%obj)            
            if multiline:
                resout="\n"
                keys=list(obj.keys())
                keys.sort()
                for key in keys:
                    val=obj[key]
                    val=Text.pythonObjToStr1line(val)
                    # resout+="%s:%s, "%(key,val)
                    resout+="    %s:%s,\n"%(key,Text.pythonObjToStr1line(val))
                resout=resout.rstrip().rstrip(",")+",\n"            
            else:
                resout=""
                keys=list(obj.keys())
                keys.sort()
                for key in keys:
                    val=obj[key]
                    val=Text.pythonObjToStr1line(val)
                    resout+="%s:%s,"%(key,val)
                resout=resout.rstrip().rstrip(",")+","
            return resout

        else:   
            raise RuntimeError("Could not convert %s to string"%obj)

    @staticmethod
    def hrd2machinetext(value,onlyone=False):
        """
        'something ' removes ''
        all spaces & commas & : inside ' '  are converted
         SPACE -> \\S
         " -> \\Q
         , -> \\K
         : -> \\D
         \\n -> \\N
        """
        for item in re.findall(matchquote, value):
            item2=item.replace(",","\\K")
            item2=item2.replace("\"","\\Q")
            item2=item2.replace(" ","\\S")
            item2=item2.replace(":","\\D")
            item2=item2.replace("\\n","\\N")
            item2=item2.replace("\n","\\N")
            item2=item2.replace("'","")
            value=value.replace(item,item2)
            if onlyone:
                return item2
        return value

    @staticmethod
    def replaceQuotes(value,replacewith):
        for item in re.findall(matchquote, value):
            value=value.replace(item,replacewith)
        return value

    @staticmethod
    def machinetext2val(value):
        """
        do reverse of:
             SPACE -> \\S
             " -> \\Q
             , -> \\K
             : -> \\D
             \\n -> return
        """
        # value=value.strip("'")
        value2=value.replace("\\K",",")
        value2=value2.replace("\\Q","\"")
        value2=value2.replace("\\S"," ")
        value2=value2.replace("\\D",":")
        value2=value2.replace("\\N","\n")
        value2=value2.replace("\\n","\n")
        change=False
        if value!=value2:
            change=True
        if value2.strip()=="":
            return value2
        if value2.strip().strip('\'').startswith("[") and value2.strip().strip('\'').endswith("]"):
            value2=value2.strip().strip('\'').strip("[]")
            res=[]
            for item in value2.split(","):
                if item.strip()=="":
                    continue
                if Text.isInt(item):                
                    item=Text.getInt(item)
                elif  Text.isFloat(item):
                    item=Text.getFloat(item)
                res.append(item)
            return res
            
        if change==False:
            if Text.isInt(value2):                
                return Text.getInt(value2)
            elif  Text.isFloat(value2):
                return Text.getFloat(value2)
        # value2=value2.replace("\n","\\n")
        return value2

    @staticmethod
    def machinetext2str(value):
        """
        do reverse of:
             SPACE -> \\S
             " -> \\Q
             , -> \\K
             : -> \\D
             \n -> \\N
        """
        value=value.replace("\\K",",")
        value=value.replace("\\Q","\"")
        value=value.replace("\\S"," ")
        value=value.replace("\\D",":")
        value=value.replace("\\N","\n")
        value=value.replace("\\n","\n")
        return value

    @staticmethod
    def getInt(text):        
        if j.basetype.string.check(text):
            text=text.strip()
            if text.lower()=="none":
                return 0
            elif text==None:
                return 0             
            elif text=="":
                return 0
            else:
                text=int(text)
        else:
            text=int(text)
        return text
    
    @staticmethod
    def getFloat(text):
        if j.basetype.string.check(text):
            text=text.strip()
            if text.lower()=="none":
                return 0.0
            elif text==None:
                return 0.0
            elif text=="":
                return 0.0
            else:
                text=float(text)
        else:
            text=float(text)
        return text

    @staticmethod
    def isFloat(text):
        text=text.strip(",").strip()
        if not text.find(".")==1:
            return False
        text=text.replace(".","")
        return text.isdigit()

    @staticmethod
    def isInt(text):
        text=text.strip(",").strip()
        return text.isdigit()

    @staticmethod
    def getBool(text):
        text=text.strip()
        if j.basetype.string.check(text):
            if text.lower()=="none":
                return False
            elif text==None:
                return False
            elif text=="":
                return False
            else:
                return False
        else:
            raise RuntimeError("input needs to be string")

    @staticmethod
    def dealWithQuote(text):
        """
        look for 'something,else' the comma needs to be converted to \k
        """
        for item in re.findall(matchquote, text):
            item2=item.replace(",","\\K")
            text=text.replace(item,item2)
        return text

    @staticmethod
    def dealWithList(text):
        """
        look for [something,2] the comma needs to be converted to \k 
        """
        for item in re.findall(matchlist, text):
            item2=item.replace(",","\\K")
            text=text.replace(item,item2)
        return text

    @staticmethod
    def getList(text,ttype=None,deserialize=False):
        """
        @type can be int,bool or float (otherwise its always str)
        """
        if text.strip()=="":
            return []        
        text=Text.dealWithQuote(text)        
        text=text.split(",")
        text=[item.strip() for item in text]
        if ttype!=None:
            ttype=ttype.lower()
            if ttype=="int":
                text=[Text.getInt(item) for item in text]
            elif ttype=="bool":
                text=[Text.getBool(item) for item in text]
            elif ttype=="float":
                text=[Text.getFloat(item) for item in text]
            else:
                j.events.inputerror_critical("type needs to be: int,bool or float","text.getlist.type")

        if deserialize:
            text=[item for item in text]

        return text

    @staticmethod
    def getDict(text,ttype=None,deserialize=False):
        """
        keys are always treated as string
        @type can be int,bool or float (otherwise its always str)
        """   
        if text.strip()=="" or text.strip()=="{}":
            return {} 
        text=Text.dealWithList(text)
        text=Text.dealWithQuote(text)
        res2={}
        for item in text.split(","):
            if item.strip()!="":
                if item.find(":")==-1:
                    raise RuntimeError("Could not find : in %s, cannot get dict out of it."%text)
                    
                key,val=item.split(":",1)
                if val.find("[")!=-1:
                    val=Text.machinetext2val(val)
                else:
                    val=val.replace("\k",",")
                    key=key.strip()
                    val=val.strip()
                res2[key]=val
        return res2
