from JumpScale import j
import time

descr = """
This jumpscript waits timeout sec (test)
"""

name = "wait"
category = "test"
organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
roles = []


def action(msg, waittime):
    j.logger.log(msg, level=5, category="test.wait")
    time.sleep(waittime)
    return msg
