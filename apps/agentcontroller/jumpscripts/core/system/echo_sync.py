from JumpScale import j

descr = """
echo (return mesg)
"""

organization = "jumpscale"
name = "echo_sync"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "echo.sync"
async=False
roles = []
log=False

def action(msg=""):
    return msg

if __name__ == "__main__":
    print action("It works")
    
    