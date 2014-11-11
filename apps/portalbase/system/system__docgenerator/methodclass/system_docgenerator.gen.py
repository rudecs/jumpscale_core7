from JumpScale import j

class system_docgenerator(j.code.classGetBase()):
    """
    Initializes the swagger entry point for listing the available APIs
    
    """
    def __init__(self):
        
        self._te={}
        self.actorname="docgenerator"
        self.appname="system"
        #system_docgenerator_osis.__init__(self)
    

        pass

    def getDocForActor(self, actorname, **kwargs):
        """
        Gets the json doc of the given actor
        param:actorname name of the actor to get documentation for
        result dict
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getDocForActor")
    

    def prepareCatalog(self, **kwargs):
        """
        result dict
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method prepareCatalog")
    
