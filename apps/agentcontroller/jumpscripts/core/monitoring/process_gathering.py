from JumpScale import j
# import copy

descr = """
gather statistics about system
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "info.gather.process"
period = 120 #always in sec
enable=True
async=True
queue='process'
log=False
roles = []

def action():
    if not hasattr(j.core, 'processmanager'):
        import JumpScale.grid.processmanager
        j.core.processmanager.loadMonitorObjectTypes()

    import time
    import psutil
    rediscl = j.clients.redis.getByInstanceName('system')

    result={}
    
    def processStopped(cacheobj):
        processOsisObject=cacheobj.db
        if processOsisObject.systempids<>[]:
            processOsisObject.systempids = []
            processOsisObject.epochstop = time.time()
        # for item in j.core.processmanager.monObjects.processobject.getProcessStatProps():
        #     itemtot="%s_total"%item
        #     cacheobj.db.__dict__[item]=0
        #     cacheobj.db.__dict__[itemtot]=0


    def aggregate(cacheobj,process_key,key,value,avg=True,ttype="N",percent=False):
        if cacheobj.db.jpdomain<>"":
            cat="js"
        else:
            cat="os"

        aggrkey="n%s.process.%s.%s.%s"%(j.application.whoAmI.nid,cat,process_key,key)

        j.system.stataggregator.set(aggrkey,value,ttype=ttype,remember=True,memonly=not(j.basetype.string.check(process_key)),percent=percent)
        if avg:
            a,m=j.system.stataggregator.getAvgMax(aggrkey)
        else:
            a=value        
        cacheobj.db.__dict__[key]=a
        return cacheobj

    def loadFromSystemProcessInfo(process_key,cacheobj,pid):
        processinfo = None
        try:
            cacheobj.p = j.system.process.getProcessObject(pid)
        except:
            cacheobj.p = None
            return
        try:
            if cacheobj.p:
                args = ['get_cpu_times', 'get_memory_info', 'create_time',
                        'get_connections', 'get_io_counters', 'getcwd',
                        'get_num_fds', 'get_num_ctx_switches', 'get_num_threads',
                        'get_cpu_percent', 'username']

                processinfo = cacheobj.p.as_dict(args)
                processinfo['parent'] = cacheobj.p.parent.pid
                processinfo['children'] = [ x.pid for x in cacheobj.p.get_children() ]
        except psutil.NoSuchProcess:
            pass
        if not processinfo:
            processinfo = {'cpu_times': (0.0, 0.0),
                           'memory_info': (0.0, 0.0),
                           'create_time': 0.0,
                           'connections': [],
                           'memory_info': (0.0, 0.0),
                           'io_counters': (0, 0, 0, 0),
                           'cwd': '',
                           'parent': 0,
                           'num_fds': 0,
                           'num_ctx_switches': (0.0, 0.0),
                           'num_threads': 0,
                           'cpu_percent': 0.0,
                           'username': '',
                           'children': []}

        cacheobj.db.systempids=[pid]

        cacheobj.db.epochstart = processinfo['create_time']

        #MEMORY
        mem_rss,mem_vms= processinfo['memory_info']

        cacheobj=aggregate(cacheobj,process_key,"mem_rss",round(mem_rss/1024/1024,1))
        cacheobj=aggregate(cacheobj,process_key,"mem_vms",round(mem_vms/1024/1024,1))

        connections = processinfo['connections']
        if len(connections)>0:
            cacheobj.db.nr_connections=len(connections)
            for c in connections:
                if c.status=="LISTEN":
                    #is server
                    port=c.local_address[1]
                    if port not in cacheobj.db.ports:
                        cacheobj.db.ports.append(port)
                    if c.remote_address<>() and c.remote_address not in cacheobj.netConnectionsIn:
                        cacheobj.netConnectionsIn.append(c.remote_address)
                if c.status=="ESTABLISHED":
                    if c.remote_address not in cacheobj.netConnectionsOut:
                        cacheobj.netConnectionsOut.append(c.remote_address)

        cacheobj=aggregate(cacheobj,process_key,"nr_connections_in",len(cacheobj.netConnectionsIn),avg=False)
        cacheobj=aggregate(cacheobj,process_key,"nr_connections_out",len(cacheobj.netConnectionsOut),avg=False)

        cacheobj.db.io_read_count, cacheobj.db.io_write_count, cacheobj.db.io_read_mbytes, cacheobj.db.io_write_mbytes = processinfo['io_counters']
        for item in ["io_read_count","io_write_count","io_read_mbytes","io_write_mbytes"]:
            cacheobj=aggregate(cacheobj,process_key,item,cacheobj.db.__dict__[item],ttype="D")

        cacheobj.db.workingdir= processinfo['cwd']
        cacheobj.db.parent= processinfo['parent']
        nr_file_descriptors = processinfo['num_fds']
        cacheobj=aggregate(cacheobj,process_key,"nr_file_descriptors",nr_file_descriptors)

        nr_ctx_switches_voluntary,nr_ctx_switches_involuntary = processinfo['num_ctx_switches']
        cacheobj=aggregate(cacheobj,process_key,"nr_ctx_switches_voluntary",nr_ctx_switches_voluntary)
        cacheobj=aggregate(cacheobj,process_key,"nr_ctx_switches_involuntary",nr_ctx_switches_involuntary)

        nr_threads=cacheobj.p.get_num_threads()
        cacheobj=aggregate(cacheobj,process_key,"nr_threads",nr_threads)

        # cacheobj.nr_openfiles=cacheobj.p.get_open_files()
        cpu_time_user,cpu_time_system= processinfo['cpu_times']
        cacheobj=aggregate(cacheobj,process_key,"cpu_time_user",cpu_time_user,ttype="D",percent=True)
        cacheobj=aggregate(cacheobj,process_key,"cpu_time_system",cpu_time_system,ttype="D",percent=True)

        cpu_percent= processinfo['cpu_percent']
        cacheobj=aggregate(cacheobj,process_key,"cpu_percent",cpu_percent,percent=True)

        cacheobj.db.user= processinfo['username']

        for childpid in processinfo['children']:
            childcache = j.core.processmanager.monObjects.processobject.get(id=childpid)
            result[childpid]=childcache
            loadFromSystemProcessInfo(childpid,childcache, childpid)
            if childpid not in j.core.processmanager.childrenPidsFound:
                if childpid not in cacheobj.children:
                    cacheobj.children.append(childcache)
                j.core.processmanager.childrenPidsFound[int(childpid)]=True

    #walk over startupmanager processes (make sure we don't double count)
    for sprocess in j.tools.startupmanager.getProcessDefs():
        pid = sprocess.getJSPid()

        if j.core.processmanager.monObjects.processobject.pid2name.has_key(pid):
            sprocess.domain,sprocess.name=j.core.processmanager.monObjects.processobject.pid2name[pid]
        
        process_key="%s_%s"%(sprocess.domain,sprocess.name)
        print "process: '%s' pid:'%s'"%(process_key,pid)

        # exists=j.core.processmanager.monObjects.processobject.exists(process_key)

        cacheobj=j.core.processmanager.monObjects.processobject.get(id=process_key)

        cacheobj.ckeyOld = rediscl.hget('processes', process_key)

        processOsisObject=cacheobj.db

        processOsisObject.active=sprocess.isRunning()
        processOsisObject.ports = sprocess.ports
        processOsisObject.jpname = sprocess.jpackage_name
        processOsisObject.jpdomain=sprocess.jpackage_domain
        processOsisObject.workingdir = sprocess.workingdir
        processOsisObject.cmd = sprocess.cmd
        processOsisObject.sname = sprocess.name
        processOsisObject.pname = ""
        processOsisObject.getSetGuid()
        processOsisObject.type="jsprocess"
        processOsisObject.statkey=process_key
        processOsisObject.systempids = sprocess.getPids()


        if processOsisObject.systempids:            
            loadFromSystemProcessInfo(process_key,cacheobj,processOsisObject.systempids[0])
            cacheobj.getTotalsChildren()
        else:
            processStopped(cacheobj)

        result[process_key]=cacheobj



        # exists=j.core.processmanager.monObjects.processobject.exists(process_key)
    for process_key,cacheobj in result.iteritems():
        if j.basetype.string.check(process_key):
            cacheobj.db.systempids.sort()
            newKey=cacheobj.db.getContentKey()
            if newKey != cacheobj.ckeyOld:                    
                print "STORE IN OSIS#########%s%s"%(cacheobj.db.pname,cacheobj.db.sname)
                cacheobj.send2osis()
                rediscl.hset('processes', process_key, newKey)


    #find deleted processes
    for process_key in j.core.processmanager.monObjects.processobject.monitorobjects.keys():

        #result is all found processobject in this run (needs to be str otherwise child obj)
        if process_key and not result.has_key(process_key):
                    
            if j.basetype.string.check(process_key):
                #no longer active
                print "NO LONGER ACTIVE:%s"%cacheobj.db.pname
                cacheobj=j.core.processmanager.monObjects.processobject.get(process_key) #is cached so low overhead

                processStopped(cacheobj)
                cacheobj.send2osis()

            #otherwise there is a memory leak
            j.core.processmanager.monObjects.processobject.monitorobjects.pop(process_key)
            #remove from aggregator
            aggrkey="n%s.process.%s"%(j.application.whoAmI.nid,process_key)
            j.system.stataggregator.delete(prefix=aggrkey)
            
    j.core.processmanager.monObjects.processobject.monitorobjects=result


if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.core.osis.getClientByInstance('processmanager')
    action()
