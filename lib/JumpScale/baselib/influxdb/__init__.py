from JumpScale import j

def cb():
    from .Influxdb import InfluxdbFactory
    return InfluxdbFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('influxdb', cb)
