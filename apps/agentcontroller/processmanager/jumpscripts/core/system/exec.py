from JumpScale import j

descr = """
Execute command
"""

organization = "jumpscale"
name = "exec"
author = "deboeckj@codscalers.com"
license = "bsd"
version = "1.0"
category = "tools"
async=True
roles = []
log=True

def action(cmd="hostname -a"):
    return j.system.process.execute(cmd, dieOnNonZeroExitCode=False)
