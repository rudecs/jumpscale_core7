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

        stderr = subprocess.STDOUT
        stdin = subprocess.PIPE
        if opts.debug:
            stdout = sys.stdout
            stderr = sys.stderr

        try:            
            self.p = psutil.Popen(self.cmds, env=self.env,cwd=self.workingdir,stdin=stdin, stdout=stdout, stderr=stderr,bufsize=0,shell=False) #f was: subprocess.PIPE
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

        #check there is a redis on port 9998 & 9999 (the new port for all)
        for port in [9998,8001]:
            if j.system.net.tcpPortConnectionTest("localhost",port):
                j.system.process.killProcessByPort(port)


        if j.system.net.tcpPortConnectionTest("localhost",9999)==False:
            jp=j.packages.find("redis")
            if not jp.isInstalled(instance="mem") and not j.system.net.tcpPortConnectionTest("localhost",9999):
                jp.install(hrddata={"redis.name":"mem","redis.port":9999,"redis.disk":"0","redis.mem":40},instance="mem")
            for name in ["mem"]:
                p=Process()
                p.domain="jumpscale"
                p.name="redis_%s"%name
                p.instance=name
                p.workingdir="/"
                p.cmds=[j.dirs.replaceTxtDirVars("$base/apps/redis/redis-server"),j.dirs.replaceTxtDirVars("$vardir/redis/%s/redis.conf"%name)]
                p.logpath=j.dirs.replaceTxtDirVars("$vardir/redis/%s/redis.log"%name)
                p.start()
                self.processes.append(p)
            if j.system.net.waitConnectionTest("localhost",9999,10)==False:
                j.events.opserror_critical("could not start redis on port 9999 inside processmanager",category="processmanager.redis.start")

        self.redis_mem=j.clients.redis.getGeventRedisClient("localhost",9999)
        # self.redis_disk=j.clients.redis.getGeventRedisClient("localhost",9998)

        self.redis_queues={}
        self.redis_queues["io"] = j.clients.redis.getGeventRedisQueue("localhost",9999,"workers:work:io")
        self.redis_queues["hypervisor"] = j.clients.redis.getGeventRedisQueue("localhost",9999,"workers:work:hypervisor")
        self.redis_queues["default"] = j.clients.redis.getGeventRedisQueue("localhost",9999,"workers:work:default")
        self.redis_queues["process"] = j.clients.redis.getGeventRedisQueue("localhost",9999,"workers:work:process")        

        j.processmanager=self

        self.hrd=j.application.instanceconfig

        acip=self.hrd.get("ac.ipaddress",default="")

        if "hekad" in self.services:
            jp=j.packages.findNewest("jumpscale","hekad")
            if not jp.isInstalled(instance="0"):
                jp.install(hrddata={},instance="hekad")

            p=Process()
            p.domain="jumpscale"
            p.name="hekad"
            p.instance=name
            p.workingdir="/opt/heka"
            p.cmds=["bin/hekad","--config=%s"%self.dir_hekadconfig]
            p.start()
            self.processes.append(p)


        if acip!="":

            if j.application.config.exists("grid.id"):
                if j.application.config.get("grid.id")=="" or j.application.config.getInt("grid.id")==0:
                    j.application.config.set("grid.id",self.hrd.get("grid.id"))

            acport=self.hrd.getInt("ac.port")
            aclogin=self.hrd.get("ac.login",default="node")
            acpasswd=self.hrd.get("ac.passwd",default="")
            acclientinstancename = self.hrd.get('agentcontroller.connection')

            #processmanager enabled
            while j.system.net.waitConnectionTest(acip,acport,2)==False:
                print("cannot connect to agentcontroller, will retry forever: '%s:%s'"%(acip,acport))

            #now register to agentcontroller
            self.acclient = j.clients.agentcontroller.get(acip, login=aclogin, passwd=acpasswd)
            res=self.acclient.registerNode(hostname=socket.gethostname(), machineguid=j.application.getUniqueMachineId())

            nid=res["node"]["id"]
            webdiskey=res["webdiskey"]
            self.hrd.set("grid.node.id",nid)

            self.hrd.set("agentcontroller.webdiskey",webdiskey)
            self.hrd.set("grid.id",res["node"]["gid"])
            self.hrd.set("grid.node.machineguid",j.application.getUniqueMachineId())
            self.hrd.set("grid.master.ip",acip)
            if aclogin=="root":
                self.hrd.set("grid.master.superadminpasswd",acpasswd)

            verifyinstall('jumpscale', 'webdis_client', args={"addr":acip,"port":7779})
            verifyinstall('jumpscale', 'osis_client', instance='processmanager', args={"osis.client.addr":acip,"osis.client.port":5544,"osis.client.login":aclogin,"osis.client.passwd":acpasswd})
            self.hrd.set("osis.connection","processmanager")
            verifyinstall('jumpscale', 'agentcontroller_client', instance=acclientinstancename, args={"agentcontroller.client.addr":acip,"agentcontroller.client.port":4444,"agentcontroller.client.login":aclogin})
            
            self.acclient=j.clients.agentcontroller.getByInstance(acclientinstancename)
        else:
            self.acclient=None
        
    def start(self):

        # self._webserverStart()        
        self._workerStart()

        j.core.grid.init()

        processmanagerGevent=True

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

def verifyinstall(domain='jumpscale', name='', instance='main', args={}):
    jps = j.packages.find(domain, name)
    if not jps:
        j.packages.install(domain=domain, name=name, instance=instance, args=args)
    else:
        jp = jps[0]
        isInstalled = j.system.fs.exists(jp.getInstance(instance).getHRDPath())
        if opts.reset or not isInstalled:
            j.packages.install(domain=domain, name=name, instance=instance, args=args)

parser = cmdutils.ArgumentParser()
parser.add_argument("-i", '--instance', default="0", help='jsagent instance', required=False)
parser.add_argument("-r", '--reset', action='store_true',help='jsagent reset', required=False,default=False)
parser.add_argument("-d", '--debug', action='store_true',help='Put JSAgent in debug mode', required=False,default=False)
parser.add_argument("-s", '--services', help='list of services to run e.g heka, agentcontroller,web', required=False,default="")

opts = parser.parse_args()


verifyinstall('jumpscale', 'jsagent', 'main')
j.application.instanceconfig = j.application.getAppInstanceHRD('jsagent', 'main')

#first start processmanager with all required stuff
pm=ProcessManager(reset=opts.reset)
processes=pm.processes
pm.services=[item.strip().lower() for item in opts.services.split(",")]


from lib.worker import Worker

#I had to do this in mother process otherwise weird issues caused by gevent !!!!!!!
j.core.osis.client = j.core.osis.getClientByInstance()

from gevent.pywsgi import WSGIServer

pm.start()

j.application.stop()
