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

        self.dir_data=j.system.fs.joinPaths(j.dirs.baseDir,"jsagent_data")
        self.dir_hekadconfig=j.system.fs.joinPaths(self.dir_data,"dir_hekadconfig")
        self.dir_actions=j.system.fs.joinPaths(self.dir_data,"actions")
        j.system.fs.createDir(self.dir_data)
        if j.system.net.tcpPortConnectionTest("localhost",9999)==False:
            redisServices = j.atyourservice.findServices('jumpscale', 'redis', 'system')
            if len(redisServices) <= 0:
                args = {'instance.param.port': 9999,
                        'instance.param.disk': 0,
                        'instance.param.mem': 40,
                        'instance.param.ip': '127.0.0.1',
                        'instance.param.passwd': '',
                        'instance.param.unixsocket': 0}
                redisService = j.atyourservice.new('jumpscale', 'redis', 'system', args=args)
                redisService.install()
            else:
                redisService = redisServices[0]
                redisService.start()
            if j.system.net.waitConnectionTest("localhost",9999,10)==False:
                j.events.opserror_critical("could not start redis on port 9999 inside processmanager",category="processmanager.redis.start")

        self.redis_mem=j.clients.redis.getByInstance('system')

        self.redis_queues={}
        self.redis_queues["io"] = self.redis_mem.getQueue("workers:work:io")
        self.redis_queues["hypervisor"] = self.redis_mem.getQueue("workers:work:hypervisor")
        self.redis_queues["default"] = self.redis_mem.getQueue("workers:work:default")
        self.redis_queues["process"] = self.redis_mem.getQueue("workers:work:process")

        j.processmanager=self

        self.hrd=j.application.instanceconfig


        acclientinstancename = self.hrd.get('instance.agentcontroller.connection')
        osisinstance = self.hrd.get('instance.osis.connection')
        osisconfig = j.application.getAppInstanceHRD('osis_client', osisinstance)
        acconfig = j.application.getAppInstanceHRD('agentcontroller_client', acclientinstancename)

        acip = acconfig.get("instance.agentcontroller.client.addr",default="")

        if acip!="":

            if j.application.config.exists("grid.id"):
                if j.application.config.get("grid.id")=="" or j.application.config.getInt("grid.id")==0:
                    j.application.config.set("grid.id",self.hrd.get("instance.grid.id"))

            acport = acconfig.getInt("instance.agentcontroller.client.port")
            aclogin = acconfig.get("instance.agentcontroller.client.login",default="node")
            acpasswd = acconfig.get("instance.agentcontroller.client.passwd",default="")

            osislogin = osisconfig.get('instance.param.osis.client.login')
            osispassword = osisconfig.get('instance.param.osis.client.passwd')

            #processmanager enabled
            while j.system.net.waitConnectionTest(acip,acport,2)==False:
                print("cannot connect to agentcontroller, will retry forever: '%s:%s'"%(acip,acport))

            #now register to agentcontroller with osis credentials
            self.acclient = j.clients.agentcontroller.get(acip, login=osislogin, passwd=osispassword, new=True)
            res=self.acclient.registerNode(hostname=socket.gethostname(), machineguid=j.application.getUniqueMachineId())

            nid=res["node"]["id"]
            jsagentService = j.atyourservice.get('jumpscale', 'jsagent', parent=None)
            jsagentService.hrd.set("grid.node.id",nid)
            j.application.config.set('grid.node.id',nid)

            jsagentService.hrd.set("grid.id",res["node"]["gid"])
            jsagentService.hrd.set("grid.node.machineguid",j.application.getUniqueMachineId())
            j.application.loadConfig()
            j.application.initWhoAmI(True)
            
            self.acclient=j.clients.agentcontroller.getByInstance(acclientinstancename)
        else:
            self.acclient=None


    def start(self):

        # self._webserverStart()        
        self._workerStart()

        j.core.grid.init()
        gevent.spawn(self._processManagerStart)

        self.mainloop()

    def _webserverStart(self):
        #start webserver
        server=PMWSServer()
        server.pm=self

        p=Process()
        p.domain="jumpscale"
        p.name="web"
        p.instance="main"
        p.workingdir="/"
        p.pythonObj=server
        p.pythonCode="self.pythonObj.start()"
        p.start()
        self.processes.append(p)

    def _processManagerStart(self):
        j.core.processmanager.start()

    def _workerStart(self):
        pwd = '/opt/jumpscale7/apps/jsagent/lib'
        for qname in ["default","io","process","hypervisor"]:
            p = Process()
            p.domain = 'workers'
            p.name = '%s' % qname
            p.instance = 'main'
            p.workingdir = pwd
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
parser.add_argument("-i", '--instance', default="0", help='jsagent instance', required=False)
parser.add_argument("-r", '--reset', action='store_true',help='jsagent reset', required=False,default=False)
parser.add_argument("-s", '--services', help='list of services to run e.g heka, agentcontroller,web', required=False,default="")

opts = parser.parse_args()

j.application.instanceconfig = j.application.getAppInstanceHRD('jsagent', 'main')

#first start processmanager with all required stuff
pm=ProcessManager(reset=opts.reset)
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
