from JumpScale import j

descr = """
Monitor worker status
"""

organization = "jumpscale"
name = 'workers_monitoring'
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
category = "monitor.workers"

period = 10 #always in sec
enable = False
async = False
roles = ["*"]
log=False

def action():

    import JumpScale.baselib.redis
    import time

    rediscl = j.clients.redis.getGeventRedisClient('127.0.0.1', 9999)
    timemap = {'default': '-1m', 'io': '-2h', 'hypervisor': '-10m','process':'-15m'}

    # prefix = 'workers__worker_'
    # workers = [ x[len(prefix):] for x in j.tools.startupmanager.listProcesses() if x.startswith(prefix) and  ]
    
    workers2 = rediscl.hgetall("workers:watchdog")

    timedout=[]
    tocheck=[]
   
    now=time.time()
    okperiod=int(now)-9

    def start(workername,pid=0):
        workerNameShort="_".join(workername.split("_")[:-1])
        #remote the restart cmd (no point restarting when just starting)
        j.tools.startupmanager.startProcess("workers",workerNameShort)

    for workername, lastactive in zip(workers2[0::2], workers2[1::2]):
        print "worker:%s "%workername,
        timeout = timemap.get(workername.split('_')[1])        

        lastactive=int(lastactive)
        
        #within 9 sec after startup we will not complain that worker is not there yet
        if lastactive==0 and  not j.core.processmanager.checkStartupOlderThan(60):
            #still in startupphase, there can be a workers till active and didn't restart yet
            print "startup phase"
            print
            continue

        if lastactive==0:
            print "watchdog=0, now +60 sec after start lets try to start."
            j.events.opserror_critical("Worker %s still in startup mode after 60s (trying to reach redis, agentcontroller)."%workername)
            continue

        if int(lastactive)>okperiod:
            #watchdog was close enough, no need to check further
            print "waiting for work"
            continue
        
        # print "\ntimeout:%s %s %s"%(timeout,j.base.time.getEpochAgo(timeout),lastactive)
        agoOK=now-int(j.base.time.getEpochAgo(timeout))
        if  int(lastactive)<agoOK :
            if lastactive==0:
                raise RuntimeError("BUG: lastactive cannot be 0.")
            # from IPython import embed
            # print "DEBUG NOW yyyyyyy"
            # embed()
            
            j.events.opserror('Worker %s seems to have timed out' % workername, 'monitoring') #is not critical
            timedout.append(workername)
            print "timeout",
            #lets kill

        tocheck.append(workername)

        print "busy or down"

    if tocheck==[]:
        return

    #workers not ok based on watchdog or we don't know e.g. still working (busy)

    cmd="ps ax|grep 'python worker.py --nodeid=%s'"%(j.application.whoAmI.nid)
    rc,out=j.system.process.execute(cmd)
    for line in out.split("\n"):        
        line=line.strip()
        if line.find("-wn ")<>-1:
            workerNameFound=line.split("-wn")[-1].strip()
            print workerNameFound,
            pid=int(line.split(" ")[0])
            if workerNameFound in timedout:                
                print "kill ",
                # from IPython import embed
                # print "DEBUG NOW kill"
                # embed()
                
                j.system.process.kill(pid)
                j.events.opserror_critical("had to kill worker, there was timeout on:%s"%workerNameFound)
                #@todo look for which job was running there and escalate this as well
                start(workerNameFound,pid=pid)

            if workerNameFound in tocheck:
                print "found"
                tocheck.pop(tocheck.index(workerNameFound))

    if len(tocheck)>0:
        for item in tocheck:
            start(item)
            