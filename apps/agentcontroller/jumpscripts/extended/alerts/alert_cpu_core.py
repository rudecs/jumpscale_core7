
from JumpScale import j

descr = """
Check on average cpu
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
license = "bsd"
version = "1.0"
period = 15*60  # always in sec
startatboot = True
order = 1
enable = True
async = True
log = False
queue ='process'
roles = ['master']


def action():
    try:
        import JumpScale.baselib.watchdog.client
    except Exception:
        return
    import JumpScale.grid.osis
    ocl = j.core.osis.getClientByInstance('main')
    scl = j.core.osis.getClientForCategory(ocl, 'system', 'stats')
    results = scl.search({'target':'smartSummarize(n*.system.cpu.percent, "1hour", "avg")', 'from': '-1h'})
    for noderesult in results:
        avgcpu, timestamp = noderesult['datapoints'][-1]
        target = noderesult['target']
        nid = int(target[len('smartSummarize(n'):].split('.')[0])
        if avgcpu > 95:
            state = 'CRITICAL'
        elif avgcpu > 80:
            state = 'WARNING'
        else:
            state = 'OK'
        j.tools.watchdog.client.send("cpu.core", state, avgcpu, nid=nid)
