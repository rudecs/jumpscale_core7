
import time
from JumpScale import j
import requests
try:
    import ujson as json
except:
    import json

import msgpack

class WebdisFactory:

    """
    """

    def __init__(self):
        self._webdis = {}

    def get(self, addr="127.0.0.1",port=7779,timeout=10):
        key = "%s_%s" % (addr, port)
        if key not in self._webdis:
            self._webdis[key] = Webdis(addr, port,timeout=timeout)
        res=self._webdis[key].ping()
        if res==False:
            j.events.opserror_critical("could not connect to webdis: '%s:%s'"%(addr,port), "webdis.connect")
        return self._webdis[key]

    def getByInstance(self, instance=None, timeout=10):
        if instance is None:
            instance = j.application.instanceconfig.get('webdis.connection')
        webdiscljp = j.packages.findNewest(name="webdis_client",domain="jumpscale")
        webdiscljp.load(instance)
        hrd = webdiscljp.hrd_instance
        ipaddr = hrd.get("addr")
        port = int(hrd.get("port"))
        return self.get(ipaddr, port, timeout)

    def check(self, addr="127.0.0.1",port=7779,timeout=1):
        key = "%s_%s" % (addr, port)
        rs = Webdis(addr, port,timeout=timeout)
        return rs.ping()

class Webdis(object):
    """
    """

    def __init__(self, addr="127.0.0.1",port=8889,timeout=10):
        self.addr=addr
        self.port=port
        self.timeout=timeout

    def execute(self,cmd,url="",data=None,die=True):
        for i in range(self.timeout*2):
            try:
                # headers = {'content-type': 'application/json'}
                # if url<>"":
                #     data2="%s/%s"%(cmd,url)
                # else:
                #     data2="%s"%cmd
                # if data<>None:
                #     data2="%s/%s"%(data2,data)
                # print "data:'%s'"%data2
                headers={}
                # if data<>None:
                #     headers = {'content-type': 'binary/octet-stream'}
                if url!="":
                    url2='http://%s:%s/%s/%s.png'%(self.addr,self.port,cmd,url)
                else:
                    url2='http://%s:%s/%s'%(self.addr,self.port,cmd)
                # print url2
                if data==None:
                    r=requests.get(url2)
                else:
                    # data=msgpack.dumps(data)                    
                    r=requests.put(url2, data=data, headers=headers)
                # if data<>None:
                #     print len(data)
                # r=requests.get('http://%s:%s/%s'%(self.addr,self.port,data2),headers=headers)
            except Exception as e:
                # print e
                if die==False:
                    return False
                if str(e).find("Max retries exceeded with url")!=-1:
                    print("Webdis not available")
                    time.sleep(0.5)
                    continue
                raise RuntimeError(e)
            
            if r.status_code==200:
                res=r.content
                if r.headers['content-type'] == 'application/x-msgpack':
                    res=msgpack.loads(res)
                    return res[cmd]
                elif r.headers['content-type'] == 'application/json':
                    res=json.loads(res)
                    return res[cmd]
                return res
                
            elif r.status_code==403:
                raise RuntimeError("Webdis could not execute %s,forbidden."%url2)
            elif r.status_code==404:
                return None
                # raise RuntimeError("Key not found")
            elif r.status_code==405:
                raise RuntimeError("Webdis could not execute %s,not supported"%url2)
            elif r.status_code==503:
                raise RuntimeError("Webdis not available for url:'%s',please restart webdis on server."%url2)                
            elif r.status_code!=200:
                print("Unknown status code webdis:%s"%r.status_code)
                raise RuntimeError("Webdis not available for url:'%s',unknown status code:'%s'."%(url2,r.status_code))
            else:
                # from IPython import embed
                # print "DEBUG NOW wedis.execute, check errorcondition"
                # embed()
                ##TODO
                pass
                
        # eco=j.errorconditionhandler.parsePythonErrorObject(e)
        j.errorconditionhandler.raiseOperationalCritical(message='Webdis is down on port %s'%self.port, category='webdis.down', \
            msgpub='', die=True, tags='', eco=None, extra=None)                

    def ping(self):
        res=self.execute('PING',die=False)
        if res==False or len(res)!=2 or res[1]!="PONG":
            return False

    def llen(self,key):
        return self.execute('LLEN',key)

    def rpush(self,key, item):
        return self.execute('RPUSH',key,item)

    def blpop(self,key, timeout="60"): #@todo timeout?
        return self.execute('BLPOP',key,0)

    def lpop(self,key):
        return self.execute('LPOP',key)

    def hkeys(self,key):
        return self.execute('HKEYS',key)

    def exists(self,key):
        return self.execute('EXISTS',key)==1
        
    def get(self,key):
        return self.execute('GET',key)

    def set(self,key,value):
        res=self.execute('SET',key,data=value)
        res=res.strip()
        if res!="+OK":
            raise RuntimeError("could not set %s"%key)

    def hset(self,hkey,key,value):
        return self.execute('HSET',"%s/%s"%(hkey,key),value)

    def hget(self,hkey,key):
        return self.execute('HGET',"%s/%s"%(hkey,key))
    
    def hgetall(self,hkey):
        return self.execute('HGETALL',hkey)

    def hdelete(self,hkey,key):
        return self.execute('HDEL',"%s/%s"%(hkey,key))

    def hexists(self,hkey,key):
        return self.execute('HEXISTS',"%s/%s"%(hkey,key))==1

    def incr(self,key):
        return self.execute('INCR',key)

    def incrby(self,key,nr):
        return self.execute('INCRBY',key,nr)

    def delete(self,key):
        return self.execute('DEL',key)

    def expire(self,key,timeout):
        return self.execute('EXPIRE',key,timeout)

