from JumpScale import j

from .PerformanceTrace import PerformanceTraceFactory

j.base.loader.makeAvailable(j, 'tools')

j.tools.performancetrace=PerformanceTraceFactory()


