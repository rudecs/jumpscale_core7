from JumpScale import j

descr = """
tell stat aggregator to cleanup history
"""

organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
category = "monitoring.aggregate"
period = 600 #always in sec
enable=False
async=False

roles = []

def action():
    j.system.stataggregator.clean()


