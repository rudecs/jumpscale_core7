from JumpScale.grid.serverbase.Exceptions import RemoteException
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

def action():
    osiscl = j.clients.osis.getNamespace('system')
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    try:
        cpuresults = osiscl.stats.search('select mean(value) from "%s_%s_cpu.percent.gauge" where time > now() - 1h group by time(1h)' % 
            (gid, nid))
        memresults = osiscl.stats.search('select mean(value) from "%s_%s_memory.percent.gauge" where time > now() - 1h group by time(1h)' % 
            (gid, nid))
    except RemoteException , e:
        return [{'category':'CPU', 'state':'ERROR', 'message':'influxdb is halted cannot access data'}]

    return get_results(cpuresults['raw']['series']) + get_results(memresults['raw']['series'])
        
 
def get_results(series):
    res = list()
    for sira in series:

        parts = sira['name'].split('.')[0]
        type = parts.split('_')[2]
        avgvalue = sira['values'][1][1]
        level = None
        result = dict()
        result ['state'] = 'OK'
        result ['message'] =  r'%s load -> last hour avergage is: %s %%' %(type.upper(), avgvalue)
        result ['category'] = 'CPU'
        if avgvalue > 95:
            level = 1
            result['state'] = 'ERROR'
        elif avgvalue > 80:
            level = 2
            result['state'] = 'WARNING'
        if level:
            #500_6_cpu.promile
            msg = '%s load -> above treshhold avgvalue last hour avergage is: %s %%' % (type.upper(), avgvalue)
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

