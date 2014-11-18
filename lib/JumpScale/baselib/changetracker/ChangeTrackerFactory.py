from JumpScale import j


from .ChangeTrackerClient import ChangeTrackerClient

class ChangeTrackerFactory:
    def __init__(self):
        self.logenable=True
        self.loglevel=5
        self._cache={}

    def get(self, gitlabName="incubaid"):
        name="%s_%s"%(blobclientName,gitlabName)
        if gitlabName in self._cache:
            return self._cache[gitlabName]
        self._cache[gitlabName]= ChangeTrackerClient(gitlabName)
        return self._cache[gitlabName]

    def _log(self,msg,category="",level=5):
        if level<self.loglevel+1 and self.logenable:
            j.logger.log(msg,category="changetracker.%s"%category,level=level)

