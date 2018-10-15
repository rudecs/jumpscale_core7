from JumpScale import j
import time
import ujson as json

PORT = 4444


class AgentControllerFactory(object):
    def __init__(self):
        self._agentControllerClients={}
        self._agentControllerProxyClients={}

    def get(self,addr=None, port=PORT, login='root', passwd=None, new=False):
        """
        @if None will be same as master
        """
        if addr is None:
            addr, port, login, passwd = self._getConnectionTuple('main')
        connection = (addr, port, login, passwd)
        if connection not in self._agentControllerClients or new:
            self._agentControllerClients[connection]=AgentControllerClient(addr, port, login, passwd)
        return self._agentControllerClients[connection]

    def _getConnectionTuple(self, instance):
        config = self.getInstanceConfig(instance)
        addr = config['addr']
        port = config['port']
        login = config.get('login')
        passwd = config.get('passwd')
        return addr, port, login, passwd

    def getInstanceConfig(self, instance=None):
        if instance is None:
            instance = j.application.instanceconfig.get('connections', {}).get('agentcontroller', 'main')
        config = j.core.config.get("agentcontroller_client", instance)
        return config

    def getByInstance(self, instance=None, new=False):
        config = self.getInstanceConfig(instance)
        return self.get(new=new, **config)

    def getProxy(self,category="core", addr=None, port=PORT, login='root', passwd=None):
        if addr is None:
            addr, port, login, passwd = self._getConnectionTuple('main')
        connection = (addr, port, login, passwd)
        if connection not in self._agentControllerProxyClients:
            self._agentControllerProxyClients[connection]=AgentControllerProxyClient(category,addr, port, login, passwd)
        return self._agentControllerProxyClients[connection]

class AgentControllerProxyClient():
    def __init__(self,category,agentControllerIP, port, login, passwd):
        self.category=category
        acconfig = j.core.config.get('agentcontroller_client', "main")
        self.ipaddr = acconfig['addr'][0]
        passwd = acconfig.get("passwd")
        login = 'root'
        client= j.servers.geventws.getClient(self.ipaddr, PORT, user=login, passwd=passwd,category="processmanager_%s"%category)
        self.__dict__.update(client.__dict__)

class AgentControllerClient():
    def __init__(self,addr, port=PORT, login='root', passwd=None):

        if isinstance(addr, basestring):
            connections = list()
            for con in addr.split(','):
                connections.append((con, port))
        elif isinstance(addr, (tuple, list)):
            connections = [ (ip, port) for ip in addr ]
        else:
            raise ValueError("AgentControllerIP shoudl be either string or iterable")

        self.ipaddr = connections[0][0]
        if login == 'root' and passwd is None:
            instances = j.application.getAppHRDInstanceNames('agentcontroller_client')
            if not instances:
                raise RuntimeError('AgentController Client must be configured')
            acconfig = j.application.getAppInstanceHRD('agentcontroller_client', instances[0])
            passwd = acconfig.get("instance.agentcontroller.client.passwd")
        if login == 'node' and passwd is None:
            passwd = j.application.getUniqueMachineId()
        client= j.servers.geventws.getHAClient(connections, user=login, passwd=passwd,category="agent", reconnect=True)
        self.__dict__.update(client.__dict__)

    def listActiveSessions(self):
        activesessions = {}
        for gidnid, session in self.listSessions().iteritems():
            # skip nodes that didnt respond in last 60 seconds
            lastpolltime = session[0]
            roles = session[1:]
            if lastpolltime < time.time() - 60:
                continue
            gridid, nid = gidnid.split('_')
            gridid, nid = int(gridid), int(nid)
            activesessions[(gridid, nid)] = roles
        return activesessions

    def execute(self,organization,name,role=None,nid=None,gid=None,timeout=60,wait=True,queue="",dieOnFailure=True,errorreport=True, args=None):
        """
        the arguments just put at end like executeWait("test",myarg=111,something=222)
        """
        args = args or dict()
        errorReportOnServer=errorreport
        if wait==True:
            errorReportOnServer=False
        result = self.executeJumpscript(organization,name,gid=gid,nid=nid,role=role,args=args,timeout=timeout,\
            wait=wait,queue=queue,errorreport=errorReportOnServer)
        if wait and result['state'] != 'OK':
            if result['state'] == 'NOWORK' and dieOnFailure:
                raise RuntimeError('Could not find agent with role:%s' %  role)
            if result['result']!="":
                ecodict=result['result']
                eco=j.errorconditionhandler.getErrorConditionObject(ddict=ecodict)
                # eco.gid=result["gid"]
                # eco.nid=result["nid"]
                # eco.jid=result["id"]

                if errorreport:
                    eco.process()

                msg="%s\n\nCould not execute %s %s for role:%s, jobid was:%s\n"%(eco,organization,name,role,result["id"])

                if errorreport:
                    print(msg)

                if dieOnFailure:
                    j.errorconditionhandler.halt(msg)

        if wait:
            return result["result"]
        else:
            return result
