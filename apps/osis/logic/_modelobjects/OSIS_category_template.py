from JumpScale import j

parentclass=j.core.osis.getOsisImplementationParentClass("_modelobjects")  #is the name of the namespace

class mainclass(parentclass):
    """
    """
    def getObject(self,ddict={}):
        obj=j.core.grid.zobjects.getModelObject(ddict=ddict)
        return obj
