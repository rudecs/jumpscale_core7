from JumpScale import j

def cb():
    from .ProcessmanagerFactory import ProcessmanagerFactory
    return ProcessmanagerFactory()

j.base.loader.makeAvailable(j, 'core')
j.core._register('processmanager', cb)
