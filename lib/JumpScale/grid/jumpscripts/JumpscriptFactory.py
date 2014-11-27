from JumpScale import j
import time
import imp
import linecache
import inspect
import JumpScale.baselib.webdis
import JumpScale.baselib.redis
import multiprocessing

class Jumpscript(object):
    def __init__(self, ddict=None, path=None):
        self._loaded = False
        self.name=""
        self.organization=""
        self.period = 0
        self.lastrun = 0
        self.source=""
        self.debug = False
        self.path=path
        self.id = None
        self.startatboot = False
        self.path = path
        self.debug=False
        self.timeout=60
        if ddict:
            ddict.pop('path', None)
            self.__dict__.update(ddict)
        if path:
            self.load()
            self.loadAttributes()

    def write(self):
        if not self.path:
            jscriptdir = j.system.fs.joinPaths(j.dirs.tmpDir,"jumpscripts")
            j.system.fs.createDir(jscriptdir)
            self.path=j.system.fs.joinPaths(jscriptdir, "%s_%s.py" % (self.organization, self.name))
        content="""
from JumpScale import j

"""
        content += self.source
        j.system.fs.writeFile(filename=self.path, contents=content)

    def load(self):
        self._loaded = True
        md5sum = j.tools.hash.md5_string(self.path)
        modulename = 'JumpScale.jumpscript_%s' % md5sum
        linecache.checkcache(self.path)
        self.module = imp.load_source(modulename, self.path)
        if self.source.find("DEBUG NOW")!=-1:
            self.debug=True

    def getDict(self):
        result = dict()
        for attrib in ('name', 'author', 'organization', 'category', 'license', 'version', 'roles', 'source', 'path', 'descr', 'queue', 'async', 'period', 'order', 'log', 'enable', 'startatboot', 'gid', 'id','timeout'):
            result[attrib] = getattr(self, attrib)
        return result

    def loadAttributes(self):
        name = getattr(self.module, 'name', "")
        if name=="":
            name=j.system.fs.getBaseName(self.path)
            name=name.replace(".py","").lower()

        source = inspect.getsource(self.module)
        self.name=name
        self.author=getattr(self.module, 'author', "unknown")
        self.organization=getattr(self.module, 'organization', "unknown")
        self.category=getattr(self.module, 'category', "unknown")
        self.license=getattr(self.module, 'license', "unknown")
        self.version=getattr(self.module, 'version', "1.0")
        self.debug=getattr(self.module, 'debug', False)
        self.roles=getattr(self.module, 'roles', [])
        self.source=source
        self.descr=self.module.descr
        self.queue=getattr(self.module, 'queue', "")
        self.async = getattr(self.module, 'async',False)
        self.period=getattr(self.module, 'period',0)
        self.order=getattr(self.module, 'order', 1)
        self.log=getattr(self.module, 'log', True)
        self.enable=getattr(self.module, 'enable', True)
        self.startatboot=getattr(self.module, 'startatboot', False)
        self.gid=getattr(self.module, 'gid', j.application.whoAmI.gid)

    def getKey(self):
        return "%s_%s" % (self.organization, self.name)

    def executeInWorker(self, *args, **kwargs):
        if not self.path:
            self.write()
        if not self._loaded:
            self.load()

        if self.debug:
            result = self.executeInProcess(*args, **kwargs)
            return result
        else:
            def helper(pipe):
                result = self.executeInProcess(*args, **kwargs)
                pipe.send(result)

            ppipe, cpipe = multiprocessing.Pipe()
            proc = multiprocessing.Process(target=helper, args=(cpipe,))
            proc.start()
            proc.join()
            return ppipe.recv()

    def executeInProcess(self, *args, **kwargs):
        try:
            return True, self.module.action(*args, **kwargs)
        except Exception as e:
            print("error in jumpscript factory: execute in process.")
            eco = j.errorconditionhandler.parsePythonErrorObject(e)
            eco.tb = None
            eco.errormessage='Exec error procmgr jumpscr:%s_%s on node:%s_%s %s'%(self.organization,self.name, \
                    j.application.whoAmI.gid, j.application.whoAmI.nid,eco.errormessage)
            eco.tags="jscategory:%s"%self.category
            eco.jid = j.application.jid
            eco.tags+=" jsorganization:%s"%self.organization
            eco.tags+=" jsname:%s"%self.name
            j.errorconditionhandler.raiseOperationalCritical(eco=eco,die=False)
            print(eco)
            return False, eco


    def execute(self, *args, **kwargs):
        """
        """
        result = None, None
        redisw = kwargs.pop('_redisw', j.clients.redisworker)

        if not self.enable:
            return
        if not self.async:
            result = list(self.executeInProcess(*args, **kwargs))
            if not result[0]:
                eco = result[1]
                eco.type = str(eco.type)
                result[1] = eco.__dict__
        else:
            #make sure this gets executed by worker
            queue = getattr(self, 'queue', 'default') #fall back to default queue if none specified
            result=redisw.execJumpscript(self.id,_timeout=self.timeout,_queue=queue,_log=self.log,_sync=False)

        self.lastrun = time.time()
        if result!=None:
            print(("ok:%s"%self.name))
        return result


class JumpscriptFactory:

    """
    """
    def __init__(self):
        self.basedir = j.system.fs.joinPaths(j.dirs.baseDir, 'apps', 'processmanager')
        secretkey = "agentcontroller.webdiskey"
        if j.application.config.exists(secretkey)==False or j.application.config.get(secretkey)=="":
            pass
            # raise RuntimeError("please configure %s" % secretkey)
        else:
            self.secret=j.application.config.get(secretkey)

    def getJSClass(self):
        return Jumpscript

    def _getWebdisConnection(self):
        return j.clients.webdis.getByInstance()

    def pushToGridMaster(self): 
        webdis = self._getWebdisConnection()
        #create tar.gz of cmds & monitoring objects & return as binary info
        #@todo make async with local workers
        import tarfile
        ppath=j.system.fs.joinPaths(j.dirs.tmpDir,"processMgrScripts_upload.tar")
        with tarfile.open(ppath, "w:bz2") as tar:
            for path in j.system.fs.walkExtended("%s/apps/agentcontroller/processmanager"%j.dirs.baseDir, recurse=1, filePattern="*.py", dirs=False):
                arcpath="processmanager/%s"%path.split("/processmanager/")[1]
                tar.add(path,arcpath)
            for path in j.system.fs.walkExtended("%s/apps/agentcontroller/jumpscripts"%j.dirs.baseDir, recurse=1, filePattern="*.py", dirs=False):
	        arcpath="jumpscripts/%s"%path.split("/jumpscripts/")[1]
                tar.add(path,arcpath)
        data=j.system.fs.fileGetContents(ppath)       
        webdis.set("%s:scripts"%(self.secret),data)  
        # scripttgz=webdis.get("%s:scripts"%(self.secret))      
        # assert data==scripttgz

    def loadFromGridMaster(self):
        print("load processmanager code from master")
        webdis = self._getWebdisConnection()

        #delete previous scripts
        item=["eventhandling","loghandling","monitoringobjects","processmanagercmds","jumpscripts"]
        for delitem in item:
            j.system.fs.removeDirTree( j.system.fs.joinPaths(self.basedir, delitem))

        #import new code
        #download all monitoring & cmd scripts


        import tarfile
        scripttgz=webdis.get("%s:scripts"%(self.secret))
        ppath=j.system.fs.joinPaths(j.dirs.tmpDir,"processMgrScripts_download.tar")

        j.system.fs.writeFile(ppath,scripttgz)
        tar = tarfile.open(ppath, "r:bz2")

        for tarinfo in tar:
            if tarinfo.isfile():
                print((tarinfo.name))
                if tarinfo.name.find("processmanager/")==0:
                    # dest=tarinfo.name.replace("processmanager/","")           
                    tar.extract(tarinfo.name, j.system.fs.getParent(self.basedir))
                if tarinfo.name.find("jumpscripts/")==0:
                    # dest=tarinfo.name.replace("processmanager/","")           
                    tar.extract(tarinfo.name, self.basedir)

        j.system.fs.remove(ppath)
