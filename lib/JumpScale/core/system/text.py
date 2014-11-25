CODEC='utf-8'
import time
from JumpScale import j
import re
matchquote = re.compile(r'\'[^\']*\'')
re_nondigit= re.compile(r'\D')
re_float = re.compile(r'[0-9]*\.[0-9]+')
re_digit = re.compile(r'[0-9]*')


class Text:
    @staticmethod
    def toStr(value, codec=CODEC):
        if isinstance(value, str):
            return value
        elif isinstance(value, str):
            return value.encode(codec)
        else:
            return str(value)

    @staticmethod
    def toAscii(value,maxlen=0):

        out=""
        for item in value:
            if ord(item)>255:
                continue
            out+=item
        if maxlen>0 and len(out)>maxlen:
            out=out[0:maxlen]
        out=out.replace("\r","")        
        return out

    @staticmethod
    def toUnicode(value, codec=CODEC):
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
    def ask(content,name=None):
        """
        look for @ASK statements in text, where found replace with input from user

        syntax for ask is:
            @ASK name:aname type:str descr:adescr default:adefault regex:aregex retry:10 minValue:10 maxValue:20 dropdownvals:1,2,3

            descr, default & regex can be between '' if spaces inside

            types are: str,float,int,bool,dropdown

            retry means will keep on retrying x times until ask is done properly

            dropdownvals is comma separated list of values to ask for when type dropdown

        @ASK can be at any position in the text

        """
        content=Text.eval(content)
        if content.strip()=="":
            return content

        endlf=content[-1]=="\n"
        
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
                    descr="Please provide value for %s"%name
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
                retry = None

            if tags.tagExists("regex"):
                regex = tags.tagGet("regex")
            else:
                regex = None

            if len(descr)>30:
                print (descr)
                descr=""

            if ttype=="str":
                result=j.console.askString(question=descr, defaultparam=default, regex=regex, retry=retry)

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
            else:
                j.events.inputerror_critical("Input type:%s is invalid (only: bool,int,str,string,dropdown,float)")

            out+="%s%s\n"%(prefix,result)

        # if endlf==False:
        out=out[:-1]

        return out

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
                    result=[str(Text.machinetext2hrd(item))  for item in string]
                elif "f" in ttypes and "b" not in ttypes:
                    result=[Text.getFloat(item) for item in string]
                elif "i" in ttypes and "b" not in ttypes:
                    result=[Text.getInt(item) for item in string]
                elif "b" == ttypes:
                    result=[Text.getBool(item) for item in string]                
                else:
                    result=[str(Text.machinetext2hrd(item)) for item in string]
            elif j.basetype.dictionary.check(string):
                ttypes=[]
                result={}
                for key,item in list(string.items()):
                    ttype,val=Text._str2var(item)
                    if ttype not in ttypes:
                        ttypes.append(ttype)
                if "s" in ttypes:                        
                    for key,item in list(string.items()):
                        result[key]=str(Text.machinetext2hrd(item)) 
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
                        result[key]=str(Text.machinetext2hrd(item)) 
            else:
                ttype,result=Text._str2var(string)
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
    def strToPythonObj(str):
        pass

    @staticmethod
    def pythonObjToStr1line(text,quote=True):
        if text==None:
            return ""
        elif j.basetype.boolean.check(text):
            if text==True:
                text="true"
            else:
                text="false"
            return text
        elif j.basetype.string.check(text):
            return Text.machinetext2hrd(text,quote)
        elif j.basetype.integer.check(text) or j.basetype.float.check(text):
            return str(text)


    @staticmethod
    def pythonObjToStr(text,multiline=True):
        """
        try to convert a python object to string representation works for None, bool, integer, float, dict, list
        """
        if text==None:
            return ""
        elif j.basetype.boolean.check(text):
            if text==True:
                text="True"
            else:
                text="False"
            return text
        elif j.basetype.string.check(text):
            if text.find("\n")!=-1 and multiline:
                text="\n%s"%Text.prefix("    ",text.strip())
            return text
        elif j.basetype.integer.check(text) or j.basetype.float.check(text):
            return str(text)
        elif j.basetype.list.check(text):
            resout=""
            for item in text:
                resout+="%s, "%Text.pythonObjToStr1line(item)
            resout=resout.strip().strip(",")            
            if len(resout)>30 and multiline:
                resout="\n"
                for item in text:
                    resout+="    %s,\n"%Text.pythonObjToStr1line(item)
                resout=resout.rstrip().strip(",")+"\n"
            return resout

        elif j.basetype.dictionary.check(text):
            resout=""
            keys=list(text.keys())
            keys.sort()
            for key in keys:
                val=text[key]
                val=Text.pythonObjToStr1line(val)
                resout+="%s:%s, "%(key,val)
            resout=resout.strip().strip(",")
            if len(resout)>30 and multiline:
                resout="\n"
                for key in keys:
                    val=text[key]
                    resout+="    %s:%s,\n"%(key,Text.pythonObjToStr1line(val))
                resout=resout.rstrip().rstrip(",")+"\n"            
            return resout
        else:
            raise RuntimeError("Could not convert %s to string"%text)

    @staticmethod
    def hrd2machinetext(value):
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
        return value

    @staticmethod
    def replaceQuotes(value,replacewith):
        for item in re.findall(matchquote, value):
            value=value.replace(item,replacewith)
        return value

    @staticmethod
    def machinetext2hrd(value,quote=False):
        """
        do reverse of:
             SPACE -> \\S
             " -> \\Q
             , -> \\K
             : -> \\D
             \\n -> \\N
        """
        value2=value.replace("\\K",",")
        value2=value2.replace("\\Q","\"")
        value2=value2.replace("\\S"," ")
        value2=value2.replace("\\D",":")
        value2=value2.replace("\\N","\n")
        value2=value2.replace("\\n","\n")
        if quote:
            change=False
            if value!=value2:
                change=True
            if change==False:
                if value.find("'")!=-1 or value.find("\n")!=-1 or value.find(":")!=-1 or value.find(",")!=-1 or value.find(" ")!=-1:
                    change=True

            if change:
                value2=value2.replace("\n","\\n")
                value="'%s'"%value2
            return value
        else:
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
            item2=item.replace(",","\\k")
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
        if text.strip()=="":
            return {} 
        text=Text.dealWithQuote(text)
        res2={}
        for item in text.split(","):
            if item.strip()!="":
                key,val=item.split(":",1)
                val=val.replace("\k",",")
                key=key.strip()
                val=val.strip()
                res2[key]=val
        return res2
