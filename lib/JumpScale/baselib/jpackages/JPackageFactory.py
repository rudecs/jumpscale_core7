from JumpScale import j

class JPackageFactory():

    def __init__(self):
        pass

    def find(self,domain="",name="",instance="",maxnr=None):
        from IPython import embed
        print ("getjp")
        embed()

    def get(self,domain="",name="",instance=""):
        jp=self.find(domain,name,instance,1)
        return jp
        
    def install(self,domain="",name="",instance="",args={}):
        jp=self.get(domain,name,instance)
        jp.install()

    def __str__(self):
        return self.__repr__()

