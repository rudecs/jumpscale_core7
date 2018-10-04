from JumpScale import j

def cb():
    from .Config import Config
    return Config()

j.base.loader.makeAvailable(j, 'core')
j.core._register('config', cb)