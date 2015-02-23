from JumpScale import j

def cb():
    from .SSLSigning import SSLSigning
    return SSLSigning()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('sslSigning', cb)
