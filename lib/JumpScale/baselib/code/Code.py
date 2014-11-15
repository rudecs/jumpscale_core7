import inspect
from JumpScale import j

from Appserver6GreenletScheduleBase import Appserver6GreenletScheduleBase
from ClassBase import ClassBase, JSModelBase, JSRootModelBase
from Appserver6GreenletBase import Appserver6GreenletBase
from Appserver6GreenletTaskletsBase import Appserver6GreenletTaskletsBase

import json #ujson.dumps does not support some arguments like separators, indent ...etc

def isPrimAttribute(obj, key):
    if key[-1]=="s":
        funcprop="new_%s"%key[:-1]
    else:
        funcprop="new_%s"%key
    isprimtype=not hasattr(obj,funcprop)
    return isprimtype, funcprop

class Code():

    def __init__(self):
        #print "HELLO"
        #@todo P2 is not lazy loading why not
        pass


    def classInfoPrint(self,classs):
        """
        print info like source code of class
        """
        filepath,linenr,sourcecode=self.classInfoGet(classs)
        print "line:%s in path:%s" % (linenr,filepath)
        print sourcecode

    def classInfoGet(self,classs):
        """
        returns filepath,linenr,sourcecode
        """
        code,nr=inspect.getsourcelines(classs.__class__)
        code="".join(code)
        path=inspect.getsourcefile(classs.__class__)
        return path,nr,code

    def classEditGeany(self,classs):
        """
        look for editor (uses geany) and then edit the file
        """
        filepath,linenr,sourcecode=self.classInfoGet(classs)
        j.system.process.executeWithoutPipe("geany %s" % filepath)

    def classEditWing(self,classs):
        """
        look for editor (uses geany) and then edit the file
        """
        filepath,linenr,sourcecode=self.classInfoGet(classs)
        j.system.process.executeWithoutPipe("wing4.1 %s" % filepath)


    def classGetBase(self):
        return ClassBase

    def classGetJSModelBase(self):
        return JSModelBase

    def classGetJSRootModelBase(self):
        return JSRootModelBase

    # def classGetAppserver6GreenletSchedule(self):
    #     return Appserver6GreenletScheduleBase

    # def classGetAppserver6Greenlet(self):
    #     return Appserver6GreenletBase

    # def classGetAppserver6GreenletTasklets(self):
    #     return Appserver6GreenletTaskletsBase

    def dict2object(self,obj,data):
        if hasattr(obj,"_dict2obj"):
            return obj._dict2obj(data)
        if isinstance(data, dict):
            for key, value in data.iteritems():
                #is for new obj functionname
                objpropname="%s"%key

                if isinstance(value, dict) and isinstance(obj.__dict__[objpropname], dict) :
                    #is a real dict (not a dict as representation of an object)
                    isprimtype, funcprop = isPrimAttribute(obj, key)
                    if not isprimtype:
                        raise RuntimeError("not supported")
                    else:
                        for valkey, valval in value.iteritems():
                            attr = getattr(obj, key)
                            attr[valkey] = valval

                elif isinstance(data[key] ,list):
                    isprimtype, funcprop = isPrimAttribute(obj, key)
                    if not isprimtype:
                        method = getattr(obj, funcprop)
                        for valval in value:
                            newobj = method()
                            self.dict2object(newobj, valval)
                    else:
                        for valval,  in value:
                            attr = getattr(obj, key)
                            attr.append(valval)

                elif isinstance(value, dict) and not isinstance(obj.__dict__[objpropname], dict) :
                    #is a dict which represents another object
                    raise RuntimeError("not supported, only 1 level deep objects")
                else:
                    obj.__dict__[objpropname]=value
            return obj
        else:
            return data


    def dict2JSModelobject(self,obj,data):
        if isinstance(data, dict):
            for key, value in data.iteritems():
                #is for new obj functionname
                objpropname="_P_%s"%key

                if isinstance(value, dict) and isinstance(obj.__dict__[objpropname], dict) :
                    #is a real dict (not a dict as representation of an object)
                    isprimtype, funcprop = isPrimAttribute(obj, key)
                    if not isprimtype:
                        method = getattr(obj, funcprop)
                        for valkey, valval in value.iteritems():
                            newobj = method(valkey)
                            self.dict2JSModelobject(newobj,valval)
                    else:
                        for valkey, valval in value.iteritems():
                            attr = getattr(obj, key)
                            attr[valkey] = valval

                elif isinstance(value ,list):
                    if key == '_meta':
                        #we do not duplicate meta
                        continue
                    isprimtype, funcprop = isPrimAttribute(obj, key)
                    if not isprimtype:
                        method = getattr(obj, funcprop)
                        for valval in value:
                            newobj = method()
                            self.dict2JSModelobject(newobj,valval)
                    else:
                        for valval in value:
                            attr = getattr(obj, key)
                            attr.append(valval)

                elif isinstance(value, dict) and not isinstance(obj.__dict__[objpropname], dict) :
                    #is a dict which represents another object
                    obj.__dict__[objpropname]= self.dict2JSModelobject(obj.__dict__[objpropname],value)
                else:
                    obj.__dict__[objpropname]=value
            return obj
        else:
            return data

    #def dict2object2(self,d):
        #if isinstance(d, dict):
            #n = {}
            #for item in d:
                #if isinstance(d[item], dict):
                    #n[item] = dict2obj(d[item])
                #elif isinstance(d[item], (list, tuple)):
                    #n[item] = [dict2obj(elem) for elem in d[item]]
                #else:
                    #n[item] = d[item]
                    #return type('obj_from_dict', (object,), n)
        #else:
            #return d

    def object2dict4index(self,obj):
        """
        convert object to a dict
        only properties on first level are considered
        and properties of basic types like int,str,float,bool,dict,list
        ideal to index the basics of an object
        """
        result={}
        def toStr(obj,possibleList=True):
            if isinstance(obj, (unicode,int,str,float,bool)) or obj==None:
                return str(obj)
            elif possibleList==True and j.basetype.list.check(obj):
                r=""
                for item in obj:
                    rr=toStr(obj,possibleList=False)
                    if rr<>"":
                        r+="%s,"%rr
                r=r.rstrip(",")
                return r
            return ""
        if isinstance(obj, ClassBase):
            for key, value in obj.__dict__.iteritems():
                if key[0:3]=="_P_":
                    key=key[3:]
                elif key[0]=="_":
                    continue
                if j.basetype.dictionary.check(value):
                    for key2 in value.keys():
                        r=toStr(value[key2])
                        if r<>"":
                            result["%s.%s" (key,key2)]=r
                else:
                    r=toStr(value)
                    if r<>"":
                        result[key]=r
        return result
        

    def object2dict(self,obj,dieOnUnknown=False,ignoreKeys=[],ignoreUnderscoreKeys=False):
        if j.basetype.dictionary.check(obj):
            return obj
        data={}

        def todict(obj,data,ignoreKeys):
            if isinstance(obj, dict):
                value={}
                for key in obj.keys():
                    if key in ignoreKeys:
                        continue
                    if ignoreUnderscoreKeys and key and key[0]=="_":
                        continue
                    value[key]=todict(obj[key],{},ignoreKeys)
                return value
            elif isinstance(obj, (tuple,list)):
                value=[]
                for item in obj:
                    value.append(todict(item,{},ignoreKeys))
                return value
            elif isinstance(obj, (int,basestring,float,bool,long)) or obj==None:
                return obj
            elif isinstance(obj, ClassBase):
                if hasattr(obj,"_obj2dict"):
                    return obj._obj2dict()
                else:
                    for key, value in obj.__dict__.iteritems():
                        if key[0:3]=="_P_":
                            key=key[3:]
                        if key in ignoreKeys:
                            continue
                        elif ignoreUnderscoreKeys and key[0]=="_":
                            continue
                        data[key] = todict(value,{},ignoreKeys)
                return data
            else:
                #from JumpScale.core.Shell import ipshellDebug,ipshell
                #print "DEBUG NOW Can only convert object to dict with properties basic types or inherited of ClassBase"
                #ipshell()
                if dieOnUnknown:
                    raise RuntimeError("Can only convert object to dict with properties basic types or inherited of ClassBase")
                try:
                    val= str(value)
                except:
                    val="__UNKNOWN__"
                return val

        out =todict(obj,data,ignoreKeys)
        # print out
        return out

    def object2yaml(self,obj):
        return j.tools.yaml.encode(self.object2dict(obj))

    def object2json(self,obj,pretty=False,skiperrors=False,ignoreKeys=[],ignoreUnderscoreKeys=False):
        obj=self.object2dict(obj,dieOnUnknown=not skiperrors,ignoreKeys=ignoreKeys,ignoreUnderscoreKeys=ignoreUnderscoreKeys)
        if pretty:            
            return json.dumps(obj, skipkeys=skiperrors, ensure_ascii=False, check_circular=True, indent=2, separators=(", ",": "),encoding='utf-8', default=None, sort_keys=True)
        else:
            return json.dumps(obj)

    def pprint(self,obj):
        result=self.object2yaml(obj)
        result=result.replace("!!python/unicode","")
        print result

    def deIndent(self,content,level=1):
        for i in range(0,level):
            content=self._deIndent(content)
        return content

    def indent(self,content,level=1):
        if not content:
            return content
        if content[-1]=="\n":
            content=content[:-1]
        lines = list()
        for line in content.splitlines():
            indent = " " * 4 * level
            lines.append("%s%s\n" % (indent, line))
        return "".join(lines)

    def _deIndent(self,content):
        #remove garbage & fix identation
        content2=""
        for line in content.split("\n"):
                if line.strip()=="":
                        content2+="\n"
                else:
                        if line.find("    ")<>0:
                                raise RuntimeError("identation error for %s."%content)
                        content2+="%s\n" % line[4:]
        return content2

