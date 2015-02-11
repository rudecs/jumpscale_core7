from JumpScale import j

descr = """
Execute command
"""

organization = "jumpscale"
name = "pyexec"
author = "hamdy.farag@codscalers.com"
license = "bsd"
version = "1.0"
category = "tools"
async=True
roles = []
log=True


"""
import psutil
result = psutil.cpu_precent()
"""
def action(cmd="result = 'It wrked'"):
    result = None
    exec(cmd)
    return result

if __name__ == "__main__":
    print action()