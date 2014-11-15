
class MethodDef(object):
    
    def __init__(self, classDef, fileDef, name="", paramstring="", comments="", decorators=[]):
        self.classDef=classDef
        self.fileDef=fileDef
        self.name=name
        self.comment=comments
        self.decorators=decorators
        self.docstring=""
        self.body=""
        self.paramstring=paramstring.strip()
        if self.paramstring != "":
            self.params = [p.strip() for p in paramstring.split(",")]
        self.decorators = []
        self.isPrivate=False

    def addLine2body(self,line=""):
        self.body=self.body+line+"\n"