from JumpScale import j


from .BlobStorClientFake import BlobStorClientFake


class BackupFactory:
    def __init__(self):
        self.logenable=True
        self.loglevel=5
        self._cache={}

    def get4Blobstor2(self, backupname,blobstorAccount,blobstorNamespace,gitlabAccount,compress=True,fullcheck=False,servercheck=True,storpath="/mnt/STOR"):
        """
        @param backupdomain is domain used in blobstor
        """
        name="%s_%s_%s_%s"%(backupname,blobstorAccount,blobstorNamespace,gitlabAccount)
        if name in self._cache:
            return self._cache[name]
        self._cache[name]= BackupClient(backupname=backupname,blobstorAccount=blobstorAccount,blobstorNamespace=blobstorNamespace, \
            gitlabAccount=gitlabAccount,compress=compress,servercheck=servercheck,fullcheck=fullcheck,storpath=storpath)
        return self._cache[name]

    def get4BlobstorLedisWeedFS(self, backupname,blobstorNamespace,compress=True,fullcheck=False,servercheck=True,storpath="/mnt/STOR"):
        """
        @param backupdomain is domain used in blobstor
        """
        name="%s_%s_%s_%s"%(backupname,"ledis_weedfs",blobstorNamespace,"")
        if name in self._cache:
            return self._cache[name]
        self._cache[name]= BlobStorClientFake(namespace=blobstorNamespace)
        return self._cache[name]

    def _log(self,msg,category="",level=5):
        if level<self.loglevel+1 and self.logenable:
            j.logger.log(msg,category="backup.%s"%category,level=level)

