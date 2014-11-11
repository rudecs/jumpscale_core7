from JumpScale import j

class system_contentmanager(j.code.classGetBase()):
    """
    this actor manages all content on the wiki
    can e.g. notify wiki/appserver of updates of content
    """
    def __init__(self):
        pass
        
        self._te={}
        self.actorname="contentmanager"
        self.appname="system"
        #system_contentmanager_osis.__init__(self)


    def bitbucketreload(self, spacename, **kwargs):
        """
        Reload all spaces from bitbucket post
        param:spacename 
        result list
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method bitbucketreload")

    def getActors(self, **kwargs):
        """
        result list(str)
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getActors")

    def getActorsWithPaths(self, **kwargs):
        """
        result list([name,path])
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getActorsWithPaths")

    def getBuckets(self, **kwargs):
        """
        result list(str)
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getBuckets")

    def getBucketsWithPaths(self, **kwargs):
        """
        result list([name,path])
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getBucketsWithPaths")

    def getContentDirsWithPaths(self, **kwargs):
        """
        return root dirs of content (actors,buckets,spaces)
        result list([name,path])
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getContentDirsWithPaths")

    def getSpaces(self, **kwargs):
        """
        result list(str)
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getSpaces")

    def getSpacesWithPaths(self, **kwargs):
        """
        result list([name,path])
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method getSpacesWithPaths")

    def modelobjectlist(self, namespace, category, key, **kwargs):
        """
        @todo describe what the goal is of this method
        param:namespace 
        param:category 
        param:key 
        result list
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method modelobjectlist")

    def modelobjectupdate(self, appname, actorname, key, **kwargs):
        """
        post args with ref_$id which refer to the key which is stored per actor in the cache
        param:appname 
        param:actorname 
        param:key 
        result html
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method modelobjectupdate")

    def notifyActorDelete(self, id, **kwargs):
        """
        param:id id of space which changed
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method notifyActorDelete")

    def notifyActorModification(self, id, **kwargs):
        """
        param:id id of actor which changed
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method notifyActorModification")

    def notifyActorNew(self, path, name, **kwargs):
        """
        param:path path of content which got changed
        param:name name
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method notifyActorNew")

    def notifyActorNewDir(self, actorname, path, actorpath='', **kwargs):
        """
        param:actorname 
        param:actorpath  default=
        param:path 
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method notifyActorNewDir")

    def notifyBucketDelete(self, id, **kwargs):
        """
        param:id id of bucket which changed
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method notifyBucketDelete")

    def notifyBucketModification(self, id, **kwargs):
        """
        param:id id of bucket which changed
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method notifyBucketModification")

    def notifyBucketNew(self, path, name, **kwargs):
        """
        param:path path of content which got changed
        param:name name
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method notifyBucketNew")

    def notifyFiledir(self, path, **kwargs):
        """
        param:path path of content which got changed
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method notifyFiledir")

    def notifySpaceDelete(self, id, **kwargs):
        """
        param:id id of space which changed
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method notifySpaceDelete")

    def notifySpaceModification(self, id, **kwargs):
        """
        param:id id of space which changed
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method notifySpaceModification")

    def notifySpaceNew(self, path, name, **kwargs):
        """
        param:path path of content which got changed
        param:name name
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method notifySpaceNew")

    def notifySpaceNewDir(self, spacename, path, spacepath='', **kwargs):
        """
        param:spacename 
        param:spacepath  default=
        param:path 
        """
        args={}
        args["spacename"]=spacename
        args["spacepath"]=spacepath
        args["path"]=path
        return self._te["notifySpaceNewDir"].execute4method(args,params={},actor=self)

    def prepareActorSpecs(self, app, actor, **kwargs):
        """
        compress specs for specific actor and targz in appropriate download location
        param:app name of app
        param:actor name of actor
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method prepareActorSpecs")

    def wikisave(self, cachekey, text, **kwargs):
        """
        param:cachekey key to the doc
        param:text content of file to edit
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method wikisave")
