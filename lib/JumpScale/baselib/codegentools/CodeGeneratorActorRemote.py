from JumpScale import j

from .CodeGeneratorBase import CodeGeneratorBase


class CodeGeneratorActorRemote(CodeGeneratorBase):

    def __init__(self, spec, typecheck=True, dieInGenCode=True, instance=0, redis=False, wsclient=None, codepath=None):
        CodeGeneratorBase.__init__(self, spec, typecheck, dieInGenCode)
        self.actorpath = j.system.fs.joinPaths(codepath, spec.appname, spec.actorname)
        j.system.fs.createDir(self.actorpath)
        self.type = "actorremote"
        self.instance = int(instance)
        self.redis = redis
        if wsclient != None:
            self.ip = wsclient.ip
            self.port = wsclient.port
            self.secret = wsclient.secret
        else:
            self.ip, self.port, self.secret = j.core.appserver6.gridmap.get(spec.appname, spec.actorname, instance)

    def addMethod(self, method):
        s = "def %s(self{paramcodestr}):\n" % method.name
        descr = ""

        if method.description != "":
            if method.description[-1] != "\n":
                method.description += "\n\n"
            descr = method.description

        for var in method.vars:
            descr += "param:%s %s" % (var.name, self.descrTo1Line(var.description))
            if var.defaultvalue != None:
                descr += " default=%s" % var.defaultvalue
            descr += "\n"

        if method.result != None:
            descr += "result %s %s\n" % (method.result.type, self.descrTo1Line(method.result.description))

        if descr != "":
            s += j.code.indent("\"\"\"\n%s\n\"\"\"\n" % descr, 1)

        paramCodeStr = ","
        for param in method.vars:
            paramCodeStr += "%s=%r," % (param.name, param.defaultvalue)
        if len(paramCodeStr) > 0 and paramCodeStr[-1] == ",":
            paramCodeStr = paramCodeStr[:-1]
        if paramCodeStr != "":
            s = s.replace("{paramcodestr}", self.descrTo1Line(paramCodeStr))
        else:
            s = s.replace("{paramcodestr}", "")

        self.content += "\n%s" % j.code.indent(s, 1)

        params = ""
        for var in method.vars:
            params += "%s=%s," % (var.name, var.name)
        if params != "" and params[-1] == ",":
            params = params[:-1]

        s = "resultcode,result=self._appserverclient.wsclient.callWebService(\"%s\",\"%s\",\"%s\",%s)" %\
            (self.spec.appname, self.spec.actorname, method.name.replace("_", "."), params)

        s += """
if resultcode != 0:
    raise RuntimeError("error in calling webservice %s:%s:%s:%s" )
else:
    if j.basetype.dictionary.check(result) and result.has_key("result"):
        return result["result"]
    else:
        return result
""" % (self.spec.appname, self.spec.actorname, method.name, params)

        s += "\nfrom JumpScale.core.Shell import ipshell\n"
        s += "ipshell()\n"

        #key="%s_%s_%s" % (spec.appname,spec.actorname,method.name)
        self.content += "\n%s" % j.code.indent(s, 2)

        return

    def generate(self):
        self.addClass()

        s = "self._appserverclient=j.clients.portal._portalClients[\"%s_%s_%s\"]" % (self.ip, self.port, self.secret)
        self.initprops += j.code.indent(s, 2)

        for method in self.spec.methods:
            self.addMethod(method)

        return self.getContent()
