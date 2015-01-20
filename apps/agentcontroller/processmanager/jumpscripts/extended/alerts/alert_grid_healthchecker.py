
from JumpScale import j

descr = """
Check on grid health
"""

organization = "jumpscale"
author = "khamisr@codescalers.com"
license = "bsd"
version = "1.0"
period = 60*15  # always in sec
startatboot = True
order = 1
enable = True
async = True
log = False
queue ='default'
roles = ['master']


def action():

    import time

    if not j.application.config.exists("grid.watchdog.addr") or j.application.config.exists("grid.watchdog.addr")=="":
        return

    import JumpScale.baselib.redis
    import JumpScale.grid.gridhealthchecker
    import JumpScale.grid.processmanager
    import JumpScale.baselib.watchdog.client
    try:
        import ujson as json
    except:
        import json

    rediscl = j.clients.redis.getGeventRedisClient('127.0.0.1', j.application.config.get('redis.port.redisp'))
    # results, errors = j.core.grid.healthchecker.runAll()

    for item in ['results','errors','lastcheck']:
        if not rediscl.hexists('healthcheck:monitoring',item):
            if not j.core.processmanager.checkStartupOlderThan(60*4):
                #can be the healthchecker did not finish yet, lets skip this round
                return

    check=True
    if not rediscl.hexists('healthcheck:monitoring','lastcheck'):
        check=False
    else:
        last=int(float(rediscl.hget('healthcheck:monitoring', 'lastcheck')))
        if last<int(time.time())-4*60:
            if not j.core.processmanager.checkStartupOlderThan(60*4):
                return
            check=False

    if check==False:
        j.tools.watchdog.client.send("grid.healthcheck","CRITICAL", gid=j.application.whoAmI.gid, nid=j.application.whoAmI.nid,value="watchdog check did not run in time.")
    errors=json.loads(rediscl.hget('healthcheck:monitoring', 'errors'))


    colormap = {'RUNNING': 'green', 'HALTED': 'red', 'UNKNOWN': 'orange',
                'BROKEN': 'red', 'OK': 'green', 'NOT OK': 'red'}

    out = '||NODE ID||NODE NAME||CATEGORY|| ||\n'
    for nid, checks in errors.iteritems():
        out += '|[*%s*|node?id=%s]|%s| | |\n' % (nid, nid, j.core.grid.healthchecker.getName(nid))
        for category, errs in checks.iteritems():
            out += '| | |%s|' % category
            for error in errs:
                defaultvalue = 'processmanager is unreachable by ping' if category == 'processmanager' else ''
                errormessage = error.get('errormessage', defaultvalue)
                for message in errormessage.split(','):
                    for status, color in colormap.iteritems():
                        message = message.replace(status, '{color:%s}*%s*{color}' % (color, status))
                    if not out.endswith('\n'):
                        out += '%s|\n' % message
                    else:
                        out += '| | | |%s|\n' % message

    state = "CRITICAL" if errors else "OK"
    j.tools.watchdog.client.send("grid.healthcheck", state, gid=j.application.whoAmI.gid, nid=j.application.whoAmI.nid, value=out, pprint=True)
