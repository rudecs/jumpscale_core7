from JumpScale import j

descr = """
echo (return msg)
"""

organization = "jumpscale"
name = "echo_sync"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "jumpscale"
async=False
roles = []
log=False

def action(msg="test"):
    return msg

if __name__ == "__main__":
    print action("It works")
