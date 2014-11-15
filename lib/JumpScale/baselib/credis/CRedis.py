
import credis
#see https://github.com/yihuang/credis
import time
from JumpScale import j
# import JumpScale.baselib.redis


from JumpScale.baselib.redis.RedisQueue import RedisQueue as CRedisQueue

#code https://github.com/yihuang/credis/blob/master/credis/base.pyx


class CRedisFactory:

    """
    """

    def __init__(self):
        self.redis = {}
        self.redisq = {}

    def getRedisClient(self, ipaddr, port,timeout=None):
        key = "%s_%s" % (ipaddr, port)
        if not self.redis.has_key(key):
            self.redis[key] = CRedis(ipaddr, port,timeout=timeout)
        return self.redis[key]

    def getRedisQueue(self, ipaddr, port, name, namespace="queues"):
        key = "%s_%s_%s_%s" % (ipaddr, port, name, namespace)
        if not self.redisq.has_key(key):
            self.redisq[key] = CRedisQueue(self.getRedisClient(ipaddr, port), name, namespace=namespace)
        return self.redisq[key]


class CRedis():
    """
    example for pipeline
     self.execute_pipeline(('SET',"test","This Should Return"),('GET',"test"))
    """

    def __init__(self, addr="127.0.0.1",port=9999,timeout=None):
        self.port=port
        self.redis=credis.Connection(host=addr,port=port,socket_timeout=timeout)
        self.connect()    
        self.fallbackredis=None

    def getFallBackRedis(self):        
        self.fallbackredis=j.clients.redis.getRedisClient(addr,port)
        #certain commands (which are not performance sensitive need normal pyredis)

    def connect(self):
        #return 100 times, max 10 sec
        for i in range(100):
            try:
                return self.redis.connect()
            except BaseException,e:
                if str(e).find("Connection refused")<>-1:
                    print "redis not available"
                    time.sleep(0.1)
                    continue
                eco=j.errorconditionhandler.parsePythonErrorObject(e)
                j.errorconditionhandler.raiseOperationalCritical(message='redis is down on port %s'%self.port, category='redis.down', msgpub='', die=True, tags='', eco=eco, extra=None)                

    def execute(self,*args):
        #return 100 times, max 10 sec
        for i in range(100):
            try:
                return self.redis.execute(*args)
            except Exception,e:
                if str(e).find("Socket closed on remote end")<>-1:
                    print "redis socket closed, retry"
                    time.sleep(0.1)
                    continue
                if str(e).find("Connection refused")<>-1:
                    self.connect()
                    time.sleep(1)
                    continue

                eco=j.errorconditionhandler.parsePythonErrorObject(e)
                j.errorconditionhandler.raiseOperationalCritical(message='redis is down on port %s'%self.port, category='redis.down', msgpub='', die=True, tags='', eco=eco, extra=None)                

    def llen(self,key):
        return self.execute('LLEN',key)

    def rpush(self,key, item):
        return self.execute('RPUSH',key,item)

    def blpop(self,key, timeout="60"): #@todo timeout?
        return self.execute('BLPOP',key,0)

    def lpop(self,key):
        return self.execute('LPOP',key)

    def keys(self,key="*"):
        return self.execute('KEYS',key)

    def hkeys(self,key):
        return self.execute('HKEYS',key)

    def exists(self,key):
        return self.execute('EXISTS',key)==1
        
    def get(self,key):
        return self.execute('GET',key)

    def set(self,key,value):
        return self.execute('SET',key,value)

    def hset(self,hkey,key,value):
        return self.execute('HSET',hkey,key,value)

    def hget(self,hkey,key):
        return self.execute('HGET',hkey,key)
    
    def hgetall(self,hkey):
        return self.execute('HGETALL',hkey)

    def hdelete(self,hkey,key):
        return self.execute('HDEL',hkey,key)

    def hdel(self, name, *keys):
        return self.execute('HDEL', name, *keys)

    def hexists(self,hkey,key):
        return self.execute('HEXISTS',hkey,key)==1

    def incr(self,key):
        return self.execute('INCR',key)

    def incrby(self,key,nr):
        return self.execute('INCRBY',key,nr)

    def delete(self,key):
        return self.execute('DEL',key)

    def expire(self,key,timeout):
        return self.execute('EXPIRE',key,timeout)

    def hincrby(self, name, key, amount=1):
        return self.execute('HINCRBY', name, key, amount)

    def brpoplpush(self, src, dst, timeout=0):
        return self.execute('BRPOPLPUSH', src, dst, timeout)

    def scriptload(self,script):
        self.getFallBackRedis()
        return self.fallbackredis.script_load(script)
        # return self.execute('SCRIPTLOAD',script)

    def evalsha(self,sha,nrkeys,*args):
        return self.execute('EVALSHA',sha,nrkeys,*args)

    def eval(self,script,nrkeys,*args):        
        return self.execute('EVAL',script,nrkeys,*args)

    def lrange(self, name, start, end):
        return self.execute('LRANGE', name, start, end)
        

