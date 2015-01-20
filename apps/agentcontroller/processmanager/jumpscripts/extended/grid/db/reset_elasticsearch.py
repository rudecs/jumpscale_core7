from JumpScale import j

descr = """
reset elastic search, start from nothing
"""

name = "reset_elasticsearch"
category = "db"
organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"
version = "1.0"
roles = []


def action():
    
    import JumpScale.baselib.elasticsearch
    cl = j.clients.elasticsearch.get()
    cl.delete_all_indexes()
    return "done"
