from JumpScale import j

from .Influxdb import InfluxdbFactory

j.base.loader.makeAvailable(j, 'clients')

j.clients.influxdb=InfluxdbFactory()


