from JumpScale import j

def cb():
    from .PerfTestToolsFactory import PerfTestToolsFactory
    return PerfTestToolsFactory()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('perftesttools', cb)
