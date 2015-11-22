
from JumpScale import j

descr = """
Check on average cpu
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
category = "monitor.healthcheck"
license = "bsd"
version = "1.0"
period = 15*60  # always in sec
timeout = period * 0.2
startatboot = True
order = 1
enable = True
async = True
log = True
queue ='process'
roles = ['master']


def action():
    osiscl = j.clients.osis.getNamespace('system')
    results = osiscl.stats.search('select value from /\d+_\d+_(cpu.percent|memory.percent).gauge/ where time > now() - 1h;')
    res = list()
    for sira in results['raw']['series']:

        parts = sira['name'].split('.')[0]
        gid, nid, type = parts.split('_')
        gid = int(gid)
        nid = int(nid)
        value = 0
        count = 0 
        for entry in sira['values']:
            value += entry[1]
            count += 1
        avgvalue = value/count
        level = None
        result = dict()
        result ['state'] = 'OK'
        result ['message'] =  '%s load -> last hour avergage is %s' % (type.upper(), avgvalue)
        result ['category'] = 'CPU'
        if avgvalue > 95:
            level = 1
            result['state'] = 'ERROR'
        elif avgvalue > 80:
            level = 2
            result['state'] = 'WARNING'
        if level:
            #500_6_cpu.promile
            msg = '%s load -> above treshhold avgvalue last hour avergage is %s' % (type.upper(), avgvalue)
            result['message'] = msg 
            eco = j.errorconditionhandler.getErrorConditionObject(msg=msg, category='monitoring', level=level, type='OPERATIONS')
            eco.nid = nid
            eco.gid = gid
            eco.process()
        res.append(result)
    return res
    
if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.clients.osis.getByInstance('main')
    print action()

