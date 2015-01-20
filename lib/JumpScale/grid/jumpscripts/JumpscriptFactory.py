from JumpScale import j
import time
import imp
import linecache
import inspect
import JumpScale.baselib.webdis
import JumpScale.baselib.redis
import multiprocessing
import tarfile
import StringIO

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
        self.timeout = None
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
        self.timeout=getattr(self.module, 'timeout', None)
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
                try:
                    result = self.executeInProcess(*args, **kwargs)
                    pipe.send(result)
                except Exception as e:
                    result = "ERROR"
                    try:
                        result = self._getECO(e)
                    except:
                        pass
                    pipe.send((False, result))

            ppipe, cpipe = multiprocessing.Pipe()
            proc = multiprocessing.Process(target=helper, args=(cpipe,))
            proc.start()
            proc.join(self.timeout)
            if proc.is_alive():
                proc.terminate()
                return False, "TIMEOUT"
            return ppipe.recv()

    def _getECO(self, e):
        eco = j.errorconditionhandler.parsePythonErrorObject(e)
        eco.tb = None
        eco.errormessage='Exec error procmgr jumpscr:%s_%s on node:%s_%s %s'%(self.organization,self.name, \
                j.application.whoAmI.gid, j.application.whoAmI.nid,eco.errormessage)
        eco.tags="jscategory:%s"%self.category
        eco.jid = j.application.jid
        eco.tags+=" jsorganization:%s"%self.organization
        eco.tags+=" jsname:%s"%self.name
        return eco

    def executeInProcess(self, *args, **kwargs):
        try:
            return True, self.module.action(*args, **kwargs)
        except Exception as e:
            print "error in jumpscript factory: execute in process."
            eco = self._getECO(e)
            print eco
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
            print("ok:%s"%self.name)
        return result


class JumpscriptFactory:

    """
    """
    def __init__(self):
        self.basedir = j.system.fs.joinPaths(j.dirs.baseDir, 'apps', 'processmanager')
        secretkey = "agentcontroller.webdiskey"
        hrd = j.application.getAppInstanceHRD('agentcontroller', 'main', 'jumpscale')
        if hrd.exists(secretkey)==False or hrd.get(secretkey)=="":
            pass
            # raise RuntimeError("please configure %s" % secretkey)
        else:
            self.secret = hrd.get(secretkey)

    def getJSClass(self):
        return Jumpscript

    def _getWebdisConnection(self):
        return j.clients.webdis.getByInstance()

    def getArchivedJumpscripts(self, bz2_compressed=True, types=('processmanager', 'jumpscripts')):
        """
        Returns the available jumpscripts in TAR format that is optionally compressed using bzip2.

        Args:
            bz2_compressed (boolean): If True then the returned TAR is bzip2-compressed
            types (sequence of str): A sequence of the types of jumpscripts to be packed in the returned archive.
                possible values in the sequence are 'processmanager', 'jumpscripts', and 'luajumpscripts'.
        """
        fp = StringIO.StringIO()
        with tarfile.open(fileobj=fp, mode='w:bz2' if bz2_compressed else 'w') as tar:
            for jumpscript_type in types:
                parent_path = '%s/apps/agentcontroller/%s' % (j.dirs.baseDir, jumpscript_type)
                for allowed_filename_extension in ('py', 'lua'):
                    for file_path in j.system.fs.walkExtended(parent_path, recurse=1, dirs=False,
                                                              filePattern='*.' + allowed_filename_extension):
                        path_in_archive = jumpscript_type + '/' + file_path.split(parent_path)[1]
                        tar.add(file_path, path_in_archive)
        return fp.getvalue()

    def pushToGridMaster(self):
        webdis = self._getWebdisConnection()
        data = self.getArchivedJumpscripts()
        webdis.set("%s:scripts"%(self.secret),data)
        # scripttgz=webdis.get("%s:scripts"%(self.secret))
        # assert data==scripttgz

    def loadFromGridMaster(self):
        print "load processmanager code from master"
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
                print(tarinfo.name)
                if tarinfo.name.find("processmanager/")==0:
                    tar.extract(tarinfo.name, j.system.fs.getParent(self.basedir))
                if tarinfo.name.find("jumpscripts/")==0:
                    tar.extract(tarinfo.name, self.basedir)

        j.system.fs.remove(ppath)
