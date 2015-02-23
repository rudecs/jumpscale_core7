from JumpScale import j

def cb():
    from .JumpscriptFactory import JumpscriptFactory
    return JumpscriptFactory()

j.base.loader.makeAvailable(j, 'core')
j.core._register('jumpscripts', cb)
