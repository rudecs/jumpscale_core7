
def populate():
    import random, time
    from JumpScale import j
    import JumpScale.grid.osis
    syscl = j.core.osis.getClientForNamespace('system')
    client = syscl.alert

    for i in range(10):
        obj = client.new()
        obj.description = 'Demo description %s' % i
        obj.descriptionpub = 'description pub %s' % i
        obj.nid = j.application.whoAmI.nid
        obj.gid = j.application.whoAmI.gid
        obj.level = random.randint(1,3) #1:critical, 2:warning, 3:info
        obj.category = 'demo.data' #dot notation e.g. machine.start.failed
        obj.tags = 'machine:%s' % i #e.g. machine:2323
        obj.state = "NEW" #["NEW","ALERT","CLOSED"]
        obj.inittime = int(time.time()) #first time there was an error condition linked to this alert
        obj.lasttime = int(time.time()) #last time there was an error condition linked to this alert
        obj.closetime = int(time.time())  #alert is closed, no longer active
        obj.nrerrorconditions = i #nr of times this error condition happened
        for x in range(i):
            eco = syscl.eco.new(nid=j.application.whoAmI.nid, gid=j.application.whoAmI.gid)
            eco.appname = 'demo'
            guid, _, _ = syscl.eco.set(eco)
            obj.errorconditions.append(guid)  #ids of errorconditions
        
        client.set(obj)