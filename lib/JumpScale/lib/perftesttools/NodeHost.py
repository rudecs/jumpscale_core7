from JumpScale import j

# import sys
# import time
# import json
# import os
# import psutil
from NodeBase import NodeBase
from MonitoringTools import MonitoringTools


class NodeHost(NodeBase,MonitoringTools):
    def __init__(self,ipaddr,sshport=22): 
        """
        is host running the hypervisor
        """
        NodeBase.__init__(self,ipaddr=ipaddr,sshport=sshport,role="host")

    def startMonitor(self,cpu=1,disks=1,net=0):  
        env={}
        env["redishost"]=self.redis.addr
        env["redisport"]=self.redis.port
        env["cpu"]=1
        env["disks"]=0
        env["net"]=0
        self.executeInScreen("monitor","js 'j.tools.perftests.monitor()'",env=env)    

