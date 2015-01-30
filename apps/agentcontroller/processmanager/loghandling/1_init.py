import time
import JumpScale.baselib.redis
from JumpScale import j

def main(q, args, params, tags, tasklet):


    log=args["logobj"]
    redis=j.clients.redis.getByInstance('system')

    log.gid = int(log.gid)

    if log.epoch==0:
        log.epoch=int(time.time())

    incrkey="%s_%s"%(log.gid,log.nid)
    log.order=redis.incr("logs:incr:%s"%incrkey,1)
    log.guid = "%s_%s_%s"%(log.gid,log.nid,log.order)

    params.result=log


    return params


def match(q, args, params, tags, tasklet):
    return True
