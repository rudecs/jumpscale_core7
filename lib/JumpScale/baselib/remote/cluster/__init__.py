from JumpScale import j

def cb():
    from .ClusterFactory import ClusterFactory
    return ClusterFactory()

j.base.loader.makeAvailable(j, 'remote')
j.remote._register('cluster', cb)
