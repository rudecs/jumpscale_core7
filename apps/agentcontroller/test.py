from JumpScale import j

j.application.start("jumpscale:agentcontrollertest")

j.logger.consoleloglevel = 5

import JumpScale.grid.agentcontroller
ac=j.clients.agentcontroller.get("127.0.0.1")
res=ac.execute("jumpscale","echo",msg="test",role="node",queue="io")
print "result of echo test:"
print res

job=ac.execute("jumpscale","echo",msg="test",role="node",queue="io",wait=False)

job=ac.waitJumpscript(jobguid=job["guid"]) #goes very fast so really no wait
print "JOB"
print job


#lets now do error (we forget the msg argument)
res=ac.execute("jumpscale","echo",role="node",queue="io")
#we will nog get here script will fail and raise error
print res


ac.listJumpscripts()

j.application.stop()

