from JumpScale import j

def cb():
    from .SpecParser import SpecParserFactory
    return SpecParserFactory()

j.base.loader.makeAvailable(j, 'core')
j.core._register('specparser', cb)
