from JumpScale import j

def cb():
    from .grafana import GrafanaFactory
    return GrafanaFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('grafana', cb)

