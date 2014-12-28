from JumpScale import j
import ujson as json

PORT = 4444

class AgentControllerFactory(object):
    def __init__(self):
        self._agentControllerClients={}
        self._agentControllerProxyClients={}

    def get(self,addr=None, port=PORT, login='root', passwd=None):
        """
        @if None will be same as master
        """
        if addr is None:
            addr, port, login, passwd = self._getConnectionTuple('main')
        connection = (addr, port, login, passwd)
        if connection not in self._agentControllerClients:
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
            instance = j.application.instanceconfig.get('agentcontroller.connection')
        accljp = j.packages.find(name="agentcontroller_client",domain="jumpscale", instance=instance)
        if len(accljp) > 0:
            accljp = accljp[0]
        else:
            j.events.inputerror_critical("Could not find agentcontroller_client instance, please install")
        accljp.load(instance=instance)
        hrd = accljp.hrd_instance
        prefix = 'agentcontroller.client.'
        result = dict()
        for key in hrd.prefix(prefix):
            attrib = key[len(prefix):]
            value = hrd.get(key)
            if attrib == 'port':
                value = int(value)
            result[attrib] = value
        return result

    def getByInstance(self, instance=None):
        config = self.getInstanceConfig(instance)
        return self.get(**config)

    def getClientProxy(self,category="jpackages", addr=None, port=PORT, login='root', passwd=None):
        if addr is None:
            addr, port, login, passwd = self._getConnectionTuple('main')
        connection = (addr, port, login, passwd)
        if connection not in self._agentControllerProxyClients:
            self._agentControllerProxyClients[connection]=AgentControllerProxyClient(category,addr, port, login, passwd)
        return self._agentControllerProxyClients[connection]

class AgentControllerProxyClient():
    def __init__(self,category,agentControllerIP, port, login, passwd):
        self.category=category
        import JumpScale.grid.geventws
        if agentControllerIP==None:
            acipkey = "grid.agentcontroller.ip"
            if j.application.config.exists(acipkey):
                self.ipaddr=j.application.config.get(acipkey)
            else:
                self.ipaddr=j.application.config.get("grid.master.ip")
        else:
            self.ipaddr=agentControllerIP
        passwd=j.application.config.get("grid.master.superadminpasswd")
        login = 'root'
        client= j.servers.geventws.getClient(self.ipaddr, PORT, user=login, passwd=passwd,category="processmanager_%s"%category)
        self.__dict__.update(client.__dict__)

class AgentControllerClient():
    def __init__(self,addr, port=PORT, login='root', passwd=None):
        import JumpScale.grid.geventws

        if isinstance(addr, str):
            connections = list()
            for con in addr.split(','):
                self.ipaddr = con
                connections.append((con, port))
        elif isinstance(addr, (tuple, list)):
            connections = [ (ip, port) for ip in addr ]
        else:
            raise ValueError("AgentControllerIP shoudl be either string or iterable")
        if login == 'root' and passwd is None:
            passwd = j.application.config.get("grid.master.superadminpasswd")
        if login == 'node' and passwd is None:
            passwd = j.application.getUniqueMachineId()
        client= j.servers.geventws.getHAClient(connections, user=login, passwd=passwd,category="agent")
        self.__dict__.update(client.__dict__)

    def execute(self,organization,name,role=None,nid=None,gid=None,timeout=60,wait=True,queue="",dieOnFailure=True,errorreport=True, args=None):
        """
        the arguments just put at end like executeWait("test",myarg=111,something=222)
        """
        args = args or dict()
        errorReportOnServer=errorreport
        if wait==True:
            errorReportOnServer=False
        result = self.executeJumpscript(organization,name,gid=gid,nid=nid,role=role,args=args,timeout=timeout,\
            wait=wait,queue=queue,transporttimeout=timeout,errorreport=errorReportOnServer)
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

