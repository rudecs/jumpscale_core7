from JumpScale import j

def cb():
    from .HttpClient import HttpClient
    return HttpClient()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('http', cb)
