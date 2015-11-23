 
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
    osis = j.core.osis.client
    gid = j.application.whoAmI.gid
    nid = j.application.whoAmI.nid
    results = osis.search('system', 'stats', 
        'select derivative(value,10s) from "%s_%s_cpu.num_ctx_switches.gauge" where time > now() - 1h ' % 
        (gid, nid))

    res=list()
    for noderesult in results['raw'].get('series', []):
        parts = noderesult['name'].split('.')[0]
        avgctx = abs(noderesult['values'][0][-1] / 3600.) #thresholds or per second
        type = parts.split('_')[2]
        diff = list()
        value = 0 
        count = 0
        for  entry in noderesult['values']:
            if entry[1]:
                value += entry[1]
                count += 1
        avgctx = value/count
        level = None
        print avgctx
        result = dict()
        result ['state'] = 'OK'
        result ['message'] = 'CPU contextswitch value is: %s per s' % avgctx
        result ['category'] = 'CPU'
        if avgctx > 100000:
            level = 1
            result ['state'] = 'ERROR'

        elif avgctx > 600000:
            level = 2
            result ['state'] = 'WARNING'

        if level:
            msg = 'CPU contextswitch is to high current value: %s per s' % avgctx
            eco = j.errorconditionhandler.getErrorConditionObject(msg=msg, category='monitoring', level=level, type='OPERATIONS')
            eco.nid = nid
            eco.gid = gid
            eco.process()

        res.append(result)
    return res

if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.clients.osis.getByInstance('main')
    print  action()
