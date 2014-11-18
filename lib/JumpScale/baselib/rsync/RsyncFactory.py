from JumpScale import j

from .Rsync import *

class RsyncFactory:
    """
    """
    def getServer(self,root):
        return RsyncServer(root)


    def getClient(self,name="",addr="localhost",port=873,login="",passwd=""):
        return RsyncClient(name,addr,port,login,passwd)

    def getClientSecret(self,addr="localhost",port=873,secret=""):
        return RsyncClientSecret(addr,port,secret)
