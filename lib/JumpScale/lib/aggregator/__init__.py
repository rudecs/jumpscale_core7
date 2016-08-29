from JumpScale import j

def aggregator():
    from  .Aggregator import Aggregator
    return Aggregator()

def realityprocess():
    from .RealityProcess import RealityProcess
    return RealityProcess()


j.tools._register('aggregator', aggregator)
j.tools._register('realityprocess', realityprocess)
