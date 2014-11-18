from JumpScale import j

descr = """
some actions doing tests
"""

#optional info
organization = "jumpscale"
author = "kristof@incubaid.com"
license = "bsd"

import time

@nojob()
def echo(msg):
    return msg

@queue("default")
@log(5)
@nojob()
def log(logmsg):
    """
    this is a logging function not doing anything but logging
    the @log makes sure all happening gets logged to the job & central logging system, std logging is off !!!
    the @nojob means will not create a job object when executing this action
    """
    j.logger.log(logmsg, level=5, category="test_category")

@queue("io")
def error():
    """
    this error will be done in queue io
    """
    return 5/0

@errorignore
def error2():
    """
    this error will be done in queue io
    """
    return 5/0


@recurring(60)
@queue("io")
@nojob()
def msg_scheduled(msg):
    """
    this will print a message each 60 seconds on worker queue io
    """
    msg="alive"
    print(msg)

@timeout(50)
def wait(ttime=5):
    """
    this will fail when ttime>10
    """
    time.sleep(ttime)

@debug
def debug():
    """
    be careful when debugging because will be done in mother process of agent, DO NEVER DO THIS IN PRODUCTION
    """
    from IPython import embed
    print("DEBUG NOW")
    embed()
    


