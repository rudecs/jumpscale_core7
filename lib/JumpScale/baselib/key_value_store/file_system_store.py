from .store import KeyValueStoreBase
from JumpScale import j
import os
# import urllib.request, urllib.parse, urllib.error

try:
    import urlparse as urllibparse
except:
    import urllib.parse as urllibparse

SAFECHARS = " "

class FileSystemKeyValueStore(KeyValueStoreBase):
    EXTENSION = ""


    def __init__(self, namespace="", baseDir=None, serializers=None):

        KeyValueStoreBase.__init__(self, serializers)

        if not baseDir:
            baseDir = j.system.fs.joinPaths(j.dirs.varDir, 'db')

        #self.id = j.application.getUniqueMachineId()
        self.dbpath = j.system.fs.joinPaths(baseDir,namespace)

        #if not j.system.fs.exists(self.dbpath):
            #j.system.fs.createDir(self.dbpath)

    def fileGetContents(self,filename):
        fp = open(filename,"r")
        data = fp.read()
        fp.close()
        return data

    def checkChangeLog(self):
        pass


    def writeFile(self,filename, contents):
        """
        Open a file and write file contents, close file afterwards
        @param contents: string (file contents to be written)
        """
        fp = open(filename,"wb")
        fp.write(contents)  #@todo P1 will this also raise an error and not be catched by the finally
        fp.close()


    def get(self, category, key):
        # self._assertExists(category, key)
        storePath = self._getStorePath(category, key)
        if not os.path.exists(storePath):
            raise KeyError("Could not find key:'%s' in category:'%s'"%(key,category))

        value = self.fileGetContents(storePath)
        return self.unserialize(value)

    def set(self, category, key, value):

        storePath = self._getStorePath(category, key,True)
        self.writeFile(storePath,self.serialize(value))

    def destroy(self,category=""):
        if category!="":
            categoryDir = self._getCategoryDir(category)
            j.system.fs.removeDirTree(categoryDir)
        else:
            j.system.fs.removeDirTree(self.dbpath)

    def delete(self, category, key):
        #self._assertExists(category, key)

        if self.exists(category, key):
            storePath = self._getStorePath(category, key)
            j.system.fs.remove(storePath)

            # Remove all empty directories up to the base of the store being the
            # directory with the store name (4 deep).
            # Path: /<store name>/<namespace>/<category>/<key[0:2]>/<key[2:4]/

            depth = 4
            parentDir = storePath

            while depth > 0:
                parentDir = j.system.fs.getParent(parentDir)

                if j.system.fs.isEmptyDir(parentDir):
                    j.system.fs.removeDir(parentDir)

                depth -= 1

    def exists(self, category, key):
        return os.path.exists(self._getStorePath(category, key))

    def list(self, category, prefix=None):
        if not self._categoryExists(category):
            return []
        categoryDir = self._getCategoryDir(category)
        filePaths = j.system.fs.listFilesInDir(categoryDir, recursive=True)
        fileNames = [j.system.fs.getBaseName(path) for path in filePaths]
        fileNames = [ urllibparse.unquote(name) for name in fileNames ]

        if prefix:
            fileNames = [name for name in fileNames if name.startswith(prefix)]

        return fileNames

    def listCategories(self):
        return j.system.fs.listDirsInDir(self.dbpath, dirNameOnly=True)

    def _categoryExists(self, category):
        categoryDir = self._getCategoryDir(category)
        return j.system.fs.exists(categoryDir)

    def _getCategoryDir(self, category):
        return j.system.fs.joinPaths(self.dbpath, category)

    def _getStorePath(self, category, key,createIfNeeded=True):
        key = j.tools.text.toStr(key)
        key = urllibparse.quote(key, SAFECHARS)
        origkey = key
        if len(key)<4:
            key = key + (4 - len(key)) * '_'

        ddir=self.dbpath+"/"+category+"/"+key[0:2]+"/"+key[2:4]

        if createIfNeeded and not os.path.exists(ddir):
            os.makedirs(ddir)

        return ddir + "/" + origkey + self.EXTENSION

