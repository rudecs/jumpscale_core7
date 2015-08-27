from JumpScale import j

import JumpScale.baselib.remote.fabric

j.system.platform.ubuntu.check()

import cuisine
from fabric.api import *

class OurCuisine():

    def __init__(self):
        self.api = cuisine
        self.fabric = j.remote.fabric.api
        j.remote.fabric.setHost()

    def connect(self,addr,port,passwd=None,login="root"):
        if passwd!="":
            env.password=passwd

        #WHY IS THIS? TELL DESPIEGK (I commented)
        # cmd="ssh-keygen -f \"/root/.ssh/known_hosts\" -R [%s]:%s"%(addr,port)
        # j.system.process.execute(cmd,dieOnNonZeroExitCode=False)

        # if j.system.net.tcpPortConnectionTest(addr,port)==False:
            # j.events.opserror_critical("Cannot SSH connect to %s:%s, port does not answer on tcp test."%(addr,port))

        self.fabric.env['user'] = login
        self.api.connect('%s:%s' % (addr,port), "root")

        env.password=passwd
        
        return self.api

    def help(self):
        C = """
import JumpScale.baselib.remote.cuisine        
#easiest way to use do:
c=j.remote.cuisine
#and then

c.user_ensure(...)
        """
        print(C)
