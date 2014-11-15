from JumpScale import j
import JumpScale.baselib.redis
import time
import ujson

class RedisStatAggregator(object):

    def __init__(self):
        self.redis = j.clients.redis.getRedisClient('127.0.0.1', 9999)

    def pushStats(self, key, data):
        data['time'] = time.time()
        data['nid'] = j.application.whoAmI.nid
        data['gid'] = j.application.whoAmI.gid
        self.redis.rpush(key, ujson.dumps(data))

    def popStats(self, key):
        with self.redis.pipeline() as pipeline:
            pipeline.lrange(key, 0, -1)
            pipeline.delete(key)
            stats = pipeline.execute()[0]
        result = list()
        for stat in stats:
            result.append(ujson.loads(stat))
        return result
