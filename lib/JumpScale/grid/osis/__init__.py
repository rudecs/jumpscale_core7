from JumpScale import j

def cb():
    import JumpScale.grid.serverbase
    from .OSISFactory import OSISFactory
    import JumpScale.baselib.hrd
    import JumpScale.baselib.key_value_store
    return OSISFactory()

def cbc():
    import JumpScale.grid.serverbase
    from .OSISFactory import OSISClientFactory
    import JumpScale.baselib.hrd
    import JumpScale.baselib.key_value_store
    return OSISClientFactory()

j.base.loader.makeAvailable(j, 'core')
j.base.loader.makeAvailable(j, 'clients')
j.clients._register('osis', cbc)
j.core._register('osis', cb)
