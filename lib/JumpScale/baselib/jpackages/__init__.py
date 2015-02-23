from JumpScale import j

def cb():
    from .JPackageFactory import JPackageFactory
    return JPackageFactory()

j._register('packages', cb)
