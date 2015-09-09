
from JumpScale import j

descr = """
Check on average cpu
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
license = "bsd"
version = "1.0"
period = 15*60  # always in sec
timeout = period * 0.2
startatboot = True
order = 1
enable = True
async = True
log = False
queue ='process'
roles = ['master']


def action():
    osis = j.core.osis.client
    results = osis.search('system', 'stats', 'select derivative(value) from /\d+_\d+_cpu.num_ctx_switches.*/ where time > now() - 1h group by time(1h)  limit 1')

    for noderesult in results['raw'].get('series', []):
        parts = noderesult['name'].split('.')[0]
        avgctx = abs(noderesult['values'][0][-1] / 3600.) #thresholds or per second
        gid, nid, type = parts.split('_')
        gid = int(gid)
        nid = int(nid)
        level = None
        print avgctx
        if avgctx > 100000:
            level = 1 
        elif avgctx > 600000:
            level = 2
        if level:
            msg = 'CPU contextswitch is to high current value %s' % avgctx
            eco = j.errorconditionhandler.getErrorConditionObject(msg=msg, category='monitoring', level=level, type='OPERATIONS')
            eco.nid = nid
            eco.gid = gid
            eco.process()

if __name__ == '__main__':
    import JumpScale.grid.osis
    j.core.osis.client = j.clients.osis.getByInstance('main')
    action()
