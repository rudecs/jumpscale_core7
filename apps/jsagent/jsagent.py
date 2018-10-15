# gevent monkey patching should be done as soon as possible dont move!
import gevent
import gevent.monkey
gevent.monkey.patch_all()

from JumpScale import j

j.application.start("jsagent")
import time
import sys
import atexit
import psutil
import os
import select
import subprocess
import JumpScale.grid.processmanager
from JumpScale.baselib import cmdutils
import JumpScale.grid.agentcontroller
import socket


processes = list()

import JumpScale.baselib.redis


class Process():
    def __init__(self):
        self.name="unknown"
        self.domain=""
        self.instance="0"
        self.pid=0
        self.workingdir=None
        self.cmds=[]
        self.env=None
        self.pythonArgs={}
        self.pythonObj=None
        self.pythonCode=None
        self.logpath=None
        self.ports=[]
        self.psstring=""
        self.sync=False
        self.restart=False
        self.p=None

    def start(self):
        if self.cmds!=[]:
            self._spawnProcess()
        if self.pythonCode!=None:
            if self.sync:
                self.do()
            else:
                self.pid=os.fork()
                if self.pid==0:
                    self.do()
                else:
                    self.refresh()

    def refresh(self):
        self.p= psutil.Process(self.pid)

    def kill(self):
        if self.p!=None:
            self.p.kill()

    def is_running(self):
        rss,vms=self.p.get_memory_info()
        return vms!=0

    def _spawnProcess(self):
        if self.logpath==None:
            self.logpath=j.system.fs.joinPaths(j.dirs.logDir,"processmanager","logs","%s_%s_%s.log"%(self.domain,self.name,self.instance))
            j.system.fs.createDir(j.system.fs.joinPaths(j.dirs.logDir,"processmanager","logs"))
            stdout = open(self.logpath,'w')
        else:
            stdout=None

        stdin = subprocess.PIPE
        stdout = sys.stdout
        stderr = sys.stderr
        cmds = self.cmds[:]  # copy cmds
        cmds.extend(['-lp', self.logpath])

        try:
            self.p = psutil.Popen(cmds, env=self.env,cwd=self.workingdir,stdin=stdin, stdout=stdout, stderr=stderr,bufsize=0,shell=False) #f was: subprocess.PIPE
            self.pid=self.p.pid
        except Exception as e:
            print("could not execute:%s\nError:\n%s"%(self,e))

        time.sleep(0.1)
        if self.is_running()==False:
            print("could not execute:%s\n"%(self))
            if j.system.fs.exists(path=self.logpath):
                log=j.system.fs.fileGetContents(self.logpath)
                print("log:\n%s"%log)

    def do(self):
        print('A new child %s' % self.name,  os.getpid())
        if self.pythonCode!=None:
            exec(self.pythonCode)

        os._exit(0)

    def __str__(self):
        return "%s"%self.__dict__

    __repr__=__str__


class ProcessManager():
    def __init__(self,reset=False):

        self.processes = list()
        self.services = list()

        if not j.system.net.waitConnectionTest("localhost",9999,10):
            j.events.opserror_critical("could not start redis on port 9999 inside processmanager",category="processmanager.redis.start")

        self.redis_mem=j.clients.redis.getByInstance('system')

        self.redis_queues={}
        self.redis_queues["io"] = self.redis_mem.getQueue("workers:work:io")
        self.redis_queues["hypervisor"] = self.redis_mem.getQueue("workers:work:hypervisor")
        self.redis_queues["default"] = self.redis_mem.getQueue("workers:work:default")
        self.redis_queues["process"] = self.redis_mem.getQueue("workers:work:process")

        j.processmanager=self

        self.config=j.application.instanceconfig

        connections = self.config.get('connections')
        if not connections:
            raise RuntimeError("Connections data not set for jsagent server")
        acclientinstancename = connections.get('agentcontroller')
        osisinstance = connections.get('osis')
        osisconfig = j.core.config.get('osis_client', osisinstance)
        acconfig = j.core.config.get('agentcontroller_client', acclientinstancename)

        if not j.application.config["grid"]["id"]:
            raise RuntimeError("Grid id should be set")

        acip = acconfig["addr"]
        if isinstance(acip, list):
            acip = acip[0]

        acport = acconfig["port"]
        osislogin = osisconfig['login']
        osispassword = osisconfig['passwd']

        #processmanager enabled
        while not j.system.net.waitConnectionTest(acip, acport,2):
            print("cannot connect to agentcontroller, will retry forever: '%s:%s'"%(acip,acport))

        #now register to agentcontroller with osis credentials
        self.acclient = j.clients.agentcontroller.get(acip, login=osislogin, passwd=osispassword, new=True)
        memory = psutil.virtual_memory().total / 1024**2
        machineguid = j.application.getUniqueMachineId()
        res=self.acclient.registerNode(hostname=socket.gethostname(), 
                                        machineguid=machineguid,
                                        memory=memory)

        nid=res["node"]["id"]
        j.application.config['grid']['node']['id'] = nid
        j.core.config.set('system', 'grid', j.application.config['grid'])
        j.application.initWhoAmI(True)

        self.acclient = j.clients.agentcontroller.getByInstance(acclientinstancename)


    def start(self):

        from JumpScale.baselib.redisworker.RedisWorker import RedisWorkerFactory
        rw = RedisWorkerFactory()
        rw.clearWorkers()
        self._workerStart()

        j.core.grid.init()
        gevent.spawn(self._processManagerStart)

        self.mainloop()

    def _processManagerStart(self):
        j.core.processmanager.start()

    def _workerStart(self):
        for qname in ["default"] * 2 + ["io", "hypervisor"] + ["process"] * 5:
            self.startWorker(qname)


    def startWorker(self, qname):
        p = Process()
        p.domain = 'workers'
        p.name = qname
        p.instance = 'main'
        p.workingdir = '/opt/jumpscale7/apps/jsagent/lib'
        p.cmds = ['python', 'worker.py', '-qn', qname, '-i', opts.instance]
        p.restart = True
        p.start()
        self.processes.append(p)

    def mainloop(self):
        i=0
        while True:
            i+=1
            # print "NEXT:%s\n"%i
            for p in self.processes[:]:
                # p.refresh()
                if p.p!=None:
                    if not p.is_running():
                        if p.restart:
                            print("%s:%s was stopped restarting" % (p.domain, p.name))
                            p.start()
                        else:
                            print("Process %s has stopped" % p)
                            p.kill()
                            self.processes.remove(p)

            time.sleep(1)
            if len(self.processes)==0:
                print("no more children")
                # return

@atexit.register
def kill_subprocesses():
    for p in processes:
        p.kill()

parser = cmdutils.ArgumentParser()
parser.add_argument("-i", '--instance', default="main", help='jsagent instance', required=False)
parser.add_argument("-r", '--reset', action='store_true',help='jsagent reset', required=False,default=False)
parser.add_argument("-s", '--services', help='list of services to run e.g heka, agentcontroller,web', required=False,default="")

opts = parser.parse_args()

j.application.instanceconfig = j.core.config.get('jsagent', opts.instance)

#first start processmanager with all required stuff
pm=ProcessManager(reset=opts.reset)
j.application.app = pm
processes=pm.processes
pm.services=[item.strip().lower() for item in opts.services.split(",")]


from lib.worker import Worker

#I had to do this in mother process otherwise weird issues caused by gevent !!!!!!!
j.core.osis.client = j.clients.osis.getByInstance()

from gevent.pywsgi import WSGIServer

try:
    pm.start()
except KeyboardInterrupt:
    print "Bye"

j.application.stop()
