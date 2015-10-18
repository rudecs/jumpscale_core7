from JumpScale import j

descr = """
echo (return mesg)
"""

organization = "jumpscale"
name = "echo_async"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "tools.echo.async"
async=True
roles = []
log=False

def action(msg=""):
	if not msg:
		msg = 'PING!'
    return msg
