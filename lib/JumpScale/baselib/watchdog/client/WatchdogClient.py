from JumpScale import j
import JumpScale.baselib.webdis
from JumpScale.baselib.watchdog import WatchdogEvent
import JumpScale.baselib.watchdog as watchdog

try:
    import ujson as json
except:
    import json


class WatchdogClient:
    def __init__(self):

        addr=j.application.config.get("grid.watchdog.addr", default=False)
        if addr==False or addr=="":
            raise RuntimeError("please configure grid.watchdog.addr in hrdconfig")

        secret=j.application.config.get("grid.watchdog.secret", default=False)
        if secret==False or secret=="":
            raise RuntimeError("please configure grid.watchdog.secret in hrdconfig")
        self.secret=secret
        self.webdis=j.clients.webdis.get(addr=addr, port=7779, timeout=1)

    def _getWatchDogEventObj(self,gid=0,nid=0,category="",state="",value=0,ecoguid="",ddict={}):
        return WatchdogEvent(gid,nid,category,state,value,ecoguid,gguid=self.secret,ddict=ddict)


    def _setWatchdogEvent(self,wde,pprint=False):
        obj=json.dumps(wde.__dict__)
        res=self.webdis.hset(watchdog.getHSetKey(wde.gguid),"%s_%s"%(wde.nid,wde.category),obj)
        if pprint:
            print wde
        return res

    def send(self,category,state,value,ecoguid="", gid=None, nid=None,pprint=False):
        gid = gid or j.application.whoAmI.gid
        nid = nid or j.application.whoAmI.nid
        wde=self._getWatchDogEventObj(gid,nid,category,state,value,ecoguid)
        return self._setWatchdogEvent(wde,pprint=pprint)


