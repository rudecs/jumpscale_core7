#!/usr/bin/env python

from JumpScale import j

j.application.start("jumpscale:workertest")

import JumpScale.baselib.redisworker

def atest(msg):
    print(msg)
    # raise RuntimeError("e")
    return msg

w=j.clients.redisworker

def test1():
    print("START")
    for i in range(10):
        job=w.execFunction( method=atest, _category='mytest', _organization='unknown', _timeout=60, _queue='default', _log=True,_sync=True, msg="this is a test")
    print(job)
    print("STOP")

print(w.getQueuedJobs())

test1()

j.application.stop()