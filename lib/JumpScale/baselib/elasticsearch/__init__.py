from JumpScale import j

def cb():
    from .Elasticsearch import ElasticsearchFactory
    return ElasticsearchFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('elasticsearch', cb)
