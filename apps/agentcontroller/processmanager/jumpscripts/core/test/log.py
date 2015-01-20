from JumpScale import j

descr = """
This jumpscript logs something (test)
"""

name = "log"
category = "test"
organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
roles = []


def action(logmsg):
    j.logger.log(logmsg, level=5, category="test_category")
    j.logger.log(logmsg, level=5)



