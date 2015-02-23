from JumpScale import j

def cb():
    from .GraphiteClient import GraphiteClient
    return GraphiteClient()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('graphite', cb)


