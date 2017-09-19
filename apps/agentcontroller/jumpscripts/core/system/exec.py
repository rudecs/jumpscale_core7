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

def action(cmd="hostname"):
    return j.system.process.execute(cmd, dieOnNonZeroExitCode=False)


if __name__ == "__main__":
    print action()
