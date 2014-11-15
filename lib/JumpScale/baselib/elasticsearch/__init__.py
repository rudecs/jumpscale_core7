from JumpScale import j
from .Elasticsearch import ElasticsearchFactory
j.base.loader.makeAvailable(j, 'clients')
j.clients.elasticsearch = ElasticsearchFactory()
