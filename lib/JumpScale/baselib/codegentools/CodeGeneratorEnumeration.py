from JumpScale import j

from .CodeGeneratorBase import CodeGeneratorBase


class CodeGeneratorEnumeration(CodeGeneratorBase):

    def __init__(self, spec, typecheck=True, dieInGenCode=True):
        CodeGeneratorBase.__init__(self, spec, typecheck, dieInGenCode)
        self.type = "enumeration"

    def getClassName(self):
        return "%s_%s" % (self.spec.actorname, self.spec.name.replace(".", "_"))

    def addClass(self):
        spec = self.spec
        s = """
from JumpScale.core.baseclasses import BaseEnumeration

class %s(BaseEnumeration):
{descr}
    def __repr__(self):
        return str(self)
    def __init__(self, level):
        self.level = level

    def __int__(self):
        return self.level
    
    def __cmp__(self, other):
        return cmp(int(self), int(other))     
        
""" % self.getClassName()

        descr = spec.description
        if descr != "" and descr[-1] != "\n":
            descr += "\n"

        nr = 0
        for enum in spec.enums:
            nr += 1
            descr += "%s:%s\n" % (enum, nr)

        descr = "\"\"\"\n%s\n\"\"\"\n" % descr
        descr = j.code.indent(descr, 1)
        s = s.replace("{descr}\n", descr)
        self.content += s

    def generate(self):
        self.addClass()
        nr = 0
        s = ""
        name = self.getClassName()
        for enum in self.spec.enums:
            nr += 1
            s += "%s.registerItem('%s',%s)\n" % (name, enum.lower(), nr)
        s += "%s.finishItemRegistration()" % name
        self.content += s
        return self.getContent()
