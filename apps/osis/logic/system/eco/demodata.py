
def populate():
    import random, time
    from JumpScale import j
    import JumpScale.grid.osis
    syscl = j.core.osis.getClientForNamespace('system')
    client = syscl.eco

    for i in range(10):
        obj = client.new(gid=1, nid=1)
        # obj.id = random.randint(1,90000000000)
        obj.errormessage='demo error message %i' % i
        obj.errormessagePub='demo errormessagePub %s ' % random.randint(1,500)
        obj.level=random.randint(1,3) #1:critical, 2:warning, 3:info
        obj.category='demo.data.%s' % random.randint(1,600) #dot notation e.g. machine.start.failed
        obj.tags='machine:%s' % i #e.g. machine:2323
        obj.code=""
        obj.funcname=""
        obj.funcfilename=""
        obj.funclinenr=0
        obj.backtrace=""
        obj.backtraceDetailed=""
        obj.extra=""
        obj.appname='DEMO %s' % random.randint(1,600) #name as used by application
        obj.aid = random.randint(1,600)
        obj.pid = random.randint(1,600)
        obj.jid = random.randint(1,600)
        obj.masterjid = random.randint(1,600)
        obj.epoch= j.base.time.getTimeEpoch()
        obj.type=str('type')
        obj.state="NEW" #["NEW","ALERT","CLOSED"]
        obj.lasttime=0 #last time there was an error condition linked to this alert
        obj.closetime=0  #alert is closed, no longer active
        obj.occurrences=i #nr of times this error condition happened

        client.set(obj)
