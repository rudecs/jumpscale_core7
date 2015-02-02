
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
    for jp in j.packages.find(domain='jumpscale') :
        instances = jp.listInstances()
        for instance in instances:
            jpinstance = jp.getInstance(instance)
            jpinstance._load()
            if not jpinstance.actions.check_up_local():
                 message = "Process %s:%s is not running" % (process.domain, process.name)
                 j.errorconditionhandler.raiseOperationalWarning(message, 'monitoring')