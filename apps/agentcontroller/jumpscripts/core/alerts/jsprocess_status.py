
from JumpScale import j

descr = """
Check if all jsprocesses are running
"""

organization = "jumpscale"
author = "deboeckj@codescalers.com"
license = "bsd"
version = "1.0"
period = 60  # always in sec
timeout = period * 0.2
order = 1
enable = True
async = True
log = False
queue ='process'
roles = []


def action():
    for jp in j.packages.find():
        instances = jp.listInstances()
        for instance in instances:
            jpinstance = jp.getInstance(instance)
            if not jpinstance.isInstalled():
                continue
            if not jpinstance.actions.check_up_local(wait=False):
                 message = "Process %s:%s:%s is not running" % (jpinstance.domain, jpinstance.name, instance)
                 j.errorconditionhandler.raiseOperationalWarning(message, 'monitoring')
                 
if __name__ == '__main__':
    action()
