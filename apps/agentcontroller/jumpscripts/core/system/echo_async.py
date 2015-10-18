from JumpScale import j

descr = """
echo (return mesg)
"""

organization = "jumpscale"
name = "echo_async"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "monitor.healthcheck"
async = True
roles = []

period = 600
log = True

def action(msg=[{'category': 'JSAgent', 'message': 'Async test', 'state': 'OK'}]):
    return msg

if __name__ == "__main__":
    print action("It works")
