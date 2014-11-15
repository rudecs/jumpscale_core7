from JumpScale import j
import time
import imp
import linecache
import inspect
import JumpScale.baselib.redis
import multiprocessing
import JumpScale.baselib.hash
import copy

class Jumpscript(object):
    """
    a jumpscript can have more than 1 action (methods in the script)
    """
    def __init__(self, ddict={}, path=None,organization="",actor=""):
        if ddict<>{}:
            self.__dict__.update(ddict)
        else:
            if path==None:
                j.events.inputerror_critical("need to specify path when creating jumpscript object","jumpscript.init.path.empty")
            self.actor=actor
            self.organization=organization
            self.period = 0
            self.source=""
            self.debug = False
            self.timeout=60
            self.queue=""
            self.log=3              #is loglevel, 0 is nothing
            self.logjob=True
            self.modtime=0          #set by central system
            self.version=0          #set by central system

            self.module=None
            self.actions={}
            self.tags={}

            self.load(path)


    def _preprocess(self,txt):
        state="start"
        tagstempl={"debug":False,"nojob":False,"queue":"default","recurring":0,"timeout":10,"log":2,"errorignore":False}
        tags=copy.copy(tagstempl)
        result={}
        out=""
        for line in txt.split("\n"):
            if line.strip()=="" or line[0]=="#":
                continue

            if line.find("@")==0:
                state="base"

            if state=="start":
                out+="%s\n"%line            

            if line.find("def")==0:
                state="def"
                name=line[4:].split("(",1)[0].strip()
                result[name]=tags
                tags=copy.copy(tagstempl)
                out+="\n"

            if state=="def":
                out+="%s\n"%line

            if state=="base" and line.find("@")==0:
                line=line[1:]
                if line.find("(")<>-1:
                    tag,val=line.split("(",1)
                    val=val.split(")",1)[0]
                    val=val.strip()
                    val=val.replace("\"","")
                else:
                    val=""
                    tag=line.strip().lower()

                if tag=="debug":
                    tags[tag]=True
                elif tag=="nojob":
                    tags[tag]=True
                elif tag=="queue":
                    tags[tag]=val
                elif tag=="recurring":
                    tags[tag]=int(val)
                elif tag=="timeout":
                    tags[tag]=int(val)
                elif tag=="log":
                    tags[tag]=int(val)

        return out,result

    def load(self,path):
        print "load jumpscript: %s"%path
        source = j.system.fs.fileGetContents(path)
        out,tags=self._preprocess(source)        
        md5sum=j.tools.hash.md5_string(out)
        modulename = 'JumpScale.jumpscript_%s' % md5sum

        codepath=j.system.fs.joinPaths(j.dirs.tmpDir,"jumpscripts","%s.py"%md5sum)
        j.system.fs.writeFile(filename=codepath,contents=out)

        linecache.checkcache(codepath)
        self.module = imp.load_source(modulename, codepath)

        self.author=getattr(self.module, 'author', "unknown")
        self.organization=getattr(self.module, 'organization', "unknown")
        self.version=getattr(self.module, 'version', 0)
        self.modtime=getattr(self.module, 'modtime', 0)
        self.descr=getattr(self.module, 'descr', "")

        #identifies the actions & tags linked to it
        self.tags=tags

        for name,val in tags.iteritems():
            self.actions[name]=eval("self.module.%s"%name)

    def getDict(self):
        ddict=copy.copy(self.__dict__)
        ddict.pop("module")
        ddict.pop("actions")
        return ddict

    def getKey(self):
        return "%s_%s_%s" % (self.organization, self.actor,self.name)

    def executeSubprocess(self, action, *args, **kwargs):

        if self.tags[action]["debug"]:
            result = self.execute(action,*args, **kwargs)
            return result
        else:
            def helper(pipe):
                result = self.execute(action,*args, **kwargs)
                pipe.send(result)

            ppipe, cpipe = multiprocessing.Pipe()
            proc = multiprocessing.Process(target=helper, args=(cpipe,))
            proc.start()
            proc.join()
            return ppipe.recv()

    def execute(self, action,*args, **kwargs):        
        j.logger.maxlevel=self.tags[action]["log"]
        if not self.tags[action]["nojob"]:
            job=None
        else:
            job=None

        #execute without creating a job
        try:
            return True, self.actions[action](*args, **kwargs)
        except Exception, e:
            print "error in jumpscript execution."
            eco = j.errorconditionhandler.parsePythonErrorObject(e)
            eco.tb = None
            eco.errormessage='Exec error procmgr jumpscr:%s_%s on node:%s_%s %s'%(self.organization,self.name, \
                    j.application.whoAmI.gid, j.application.whoAmI.nid,eco.errormessage)
            if job<>None:
                eco.jid = job.id
            eco.tags+=" jsorganization:%s"%self.organization
            eco.tags+=" jsname:%s"%self.name
            j.errorconditionhandler.raiseOperationalCritical(eco=eco,die=False)
            print eco
            return False, eco

        if job<>None:
            pass


    def executeInWorker(self, action, *args, **kwargs):
        """
        """
        result = None, None
        redisw = kwargs.pop('_redisw', j.clients.redisworker)

        if not self.enable:
            return
        if not self.async:
            result = list(self.execute(*args, **kwargs))
            if not result[0]:
                eco = result[1]
                eco.type = str(eco.type)
                result[1] = eco.__dict__
        else:
            #make sure this gets executed by worker
            queue = getattr(self, 'queue', 'default') #fall back to default queue if none specified
            result=redisw.execJumpscript(self.id,_timeout=self.timeout,_queue=queue,_log=self.log,_sync=False)

        self.lastrun = time.time()
        if result<>None:
            print "ok:%s"%self.name
        return result

