
def main(q, args, params, tags, tasklet):

    params.result=args["eco"]

    eco=args["eco"]
    # redis=j.clients.redis.getRedisClient("127.0.0.1",9999)

    eco.gid = int(eco.gid)


    if eco.epoch==0:
        eco.epoch=int(time.time())

    # if eco.pid<>0:
    #     # hincrby(name, key, amount=1)
    #     incrkey="%s_%s"%(eco.gid,eco.pid)
    #     eco.id=redis.incr("eco:incr:%s"%incrkey,1)
    #     eco.guid = "%s_%s_%s"%(eco.gid,eco.pid,eco.order)
    # else:
    #     incrkey="%s_%s_%s"%(eco.gid,eco.nid,eco.epoch)
    #     eco.id=redis.incr("eco:incr:%s"%incrkey,1)
    #     eco.guid = "%s_%s_%s_%s"%(eco.gid,eco.nid,eco.epoch,eco.order)


    return params


def match(q, args, params, tags, tasklet):
    return True
