from JumpScale import j

def cb():
    from .AtYourServiceFactory import AtYourServiceFactory
    return AtYourServiceFactory()

j._register('atyourservice', cb)
