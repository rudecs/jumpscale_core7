from JumpScale import j

from MonitorTools import NodeBase
from MonitorTools import NodeHost
from MonitorTools import NodeMaster
import os

class PerfTestToolsFactory(object):
    """
    j.tools.perftesttools.getNodeMonitor("localhost",22)
    make sure there is influxdb running on monitor node (root/root)
    make sure there is redis running on monitor node with passwd as specified

    for example script
    call self.getScript()


    """
    def __init__(self):
        self.monitorNodeIp=None
        self.monitorNodeAddr=None
        self.redispasswd=""

    def init(self,monitorNodeIp, sshPort, redispasswd="",sshkey=""):
        self.monitorNodeIp=monitorNodeIp
        self.monitorNodeSSHPort=sshPort
        self.redispasswd=redispasswd
        self.sshkey=sshkey

    def getNodeNAS(self, ipaddr,sshport=22,nrdisks=0,fstype="xfs", role=''):
        return NodeBase(ipaddr=ipaddr, sshport=sshport, nrdisks=nrdisks, fstype=fstype, role=role)
        
    def getNodeHost(self, ipaddr,sshport=22):
        return NodeHost(ipaddr,sshport)

    def getNodeMonitor(self, ipaddr,sshport=22):
        return NodeMaster(ipaddr,sshport)

    def getExampleScript(self,path=None):
        dirpath=j.system.fs.getDirName(os.path.realpath(__file__))
        path2="%s/exampleScriptexampleScript"%dirpath
        C=j.system.fs.fileGetContents(path2)
        if path!=None:
            j.system.fs.writeFile(filename=path,contents=C)
        return C

    def monitor(self):
        """
        will do monitoring & send results to redis, env is used to get config parameters from
        """
        pass

    def influxpump(self):
        """
        will dump redis stats into influxdb & env is used to get config parameters from
        influxdb is always on localhost & std login/passwd
        """
        pass
