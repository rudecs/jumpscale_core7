from JumpScale import j

# import sys
# import time
# import json
# import os
# import psutil



class NodeBase():
    def __init__(self,ipaddr,sshport=22,redis=None,role=None):
        """
        existing roles
        - vnas
        - monitor
        - host

        """

        self.redis = redis

        self.ipaddr=ipaddr

        self.ssh=j.remote.ssh.getSSHClientUsingSSHAgent(host=ipaddr, username='root', port=sshport, timeout=10)
        # self.sal=j.ssh.unix.get(self.ssh)
        self.role=role

        self.ssh.execute("tmux kill-session -t monitor", dieOnError=False)
        self.ssh.execute("tmux new-session -d -s monitor -n monitor", dieOnError=False)

    def execute(self,cmd, env={},dieOnError=False):
        self.ssh.execute(cmd, dieOnError=dieOnError,env=env)

    def executeInScreen(self,screenname,cmd,env={}):
        """
        gets executed in right screen for the disk
        """
        if env!={}:
            #prepare export arguments
            envstr="export "
            for key,val in env.iteritems():
                envstr+="%s=%s;"%(key,val)
            envstr=envstr.strip(";")
        cmd1="cd /tmp;%s;%s"%(envstr,cmd)
        cmd2="tmux send-keys -t '%s' '%s\n'"%(screenname,cmd1)
        print "execute:'%s' on %s in screen:%s"%(cmd1,self,screenname)
        self.execute(cmd2)

    def __str__(self):
        return "node:%s"%self.ipaddr

    def __repr__(self):
        return self.__str__()
