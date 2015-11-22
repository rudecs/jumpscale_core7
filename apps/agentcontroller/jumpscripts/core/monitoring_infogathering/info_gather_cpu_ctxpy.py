 
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
    osis = j.core.osis.client
    results = osis.search('system', 'stats', 'select value from /\d+_\d+_cpu.num_ctx_switches.*/ where time > now() - 1h ')
    res=list()
    for noderesult in results['raw'].get('series', []):
        parts = noderesult['name'].split('.')[0]
        avgctx = abs(noderesult['values'][0][-1] / 3600.) #thresholds or per second
        gid, nid, type = parts.split('_')
        gid = int(gid)
        nid = int(nid)
        diff = list()
        for  i, val in enumerate(noderesult['values']):
            if i == len(noderesult['values'])-1:
                break 
            diff.append(noderesult['values'][i+1][1]-val[1])
        if diff:
            avgctx = sum(diff)/float(len(diff))
        else:
            avgctx = 0.0
        level = None
        print avgctx
        result = dict()
        result ['state'] = 'OK'
        result ['message'] = 'CPU contextswitch value is  %s' % avgctx
        result ['category'] = 'CPU'
        if avgctx > 100000:
            level = 1
            result ['state'] = 'ERROR'

        elif avgctx > 600000:
            level = 2
            result ['state'] = 'WARNING'

        if level:
            msg = 'CPU contextswitch is to high current value %s' % avgctx
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
