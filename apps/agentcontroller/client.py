from JumpScale import j

import httplib
import thread
import time

import JumpScale.grid.agentcontroller

import sys

j.application.start("jumpscale:agentcontrollertest")
j.application.initGrid()

j.logger.consoleloglevel = 5


client=j.clients.agentcontroller.get("127.0.0.1")

#execute something on own node
res= client.executeJumpscript(organization='jumpscale', name='getnetworkinfo', gid=j.application.whoAmI.gid,nid=j.application.whoAmI.nid, \
    role=None, args={}, all=False, timeout=600, wait=True, queue='', errorreport=True)

print  client.executeJumpscript(organization='jumpscale', name='error',gid=j.application.whoAmI.gid,nid=j.application.whoAmI.nid)

res= client.executeJumpscript(organization='jumpscale', name='echo',args={"msg":"something"},role="role1")

print "return based on role this time"
print res

j.application.stop()

print "start test"
for i in range(1):
    print i
    args={}
    args["msg"]="test"
    result=client.executeJumpscript(organization="jumpscale", name="echo", nid=j.application.whoAmI.nid, role=None, args=args, all=False, timeout=600, wait=True, queue='io', transporttimeout=5, _agentid=0)
    print result

j.application.stop()

print "start test"
for i in range(1):
    job=client.execute("opencode","dummy","node",args={"msg":"amessage"},timeout=60,wait=True,lock="alock")
    
    resultcode,result=client.waitJumpscript(job.id)

if job["resultcode"]>0:
    eco= j.errorconditionhandler.getErrorConditionObject(ddict=job["result"])
    eco.process()
else:
    print "result:%s"%job["result"]


