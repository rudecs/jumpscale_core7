
from JumpScale import j
import PropertyDef

class ClassDef:
    
    def __init__(self, filePath, name="", inheritance="", comments=""):
        self.filePath=filePath
        self.name=name
        self.comment=comments
        self.inheritanceString=inheritance.strip()
        if self.inheritanceString == "":
            self.inheritedClasses = []
        else:
            self.inheritedClasses = [c.strip() for c in inheritance.split(",")]
            
        self.docstring=""
        self.propertyDefs=[]
        self.methodDefs=[]
        self.preinitEntries = [] # Will contain a list of dicts, representing instances of the class to be pre-initialized. The dicts contain key/value pairs representing the membername/defaultvalue of the instances.
        self.code="" #content of file describing class

    def addPropertyDef(self,prop):
        self.propertyDefs.append(prop)

    def addMethodDef(self,method):
        self.methodDefs.append(method)

    def getProp(self, propname, includeInheritedClasses = False):
        """
        Returns the propertyDef of the property with the given name.
        Returns None if the property could not be found.
        """
        for propdef in self.propertyDefs:
            if propdef.name==propname:
                return propdef
        if includeInheritedClasses:
            for c in self.inheritedClasses:
                classDef = self.codeFile.codeStructure.getClass(c)
                pd = classDef.getProp(propname, True)
                if not pd == None:
                    return pd
        j.logger.log("Could not find the property [%s]" % propname, 3)
        return None