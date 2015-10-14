from JumpScale import j

descr = """
echo (return mesg)
"""

organization = "jumpscale"
name = "echo_sync"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"
async=False
roles = []
log=True
period=600

def action(msg=[{'category': 'JSAgent', 'message': 'Sync test', 'state': 'OK'}]):
    return msg

if __name__ == "__main__":
    print action("It works")
    
    