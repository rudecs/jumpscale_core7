from JumpScale import j

def cb():
    from .PerformanceTrace import PerformanceTraceFactory
    return PerformanceTraceFactory()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('performancetrace', cb)


