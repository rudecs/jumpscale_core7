from JumpScale import j

def bb():
    from .Bitbucket import Bitbucket
    from .BitbucketConfigManagement import BitbucketConfigManagement
    obj = Bitbucket()
    obj._config = BitbucketConfigManagement()
    return obj

def bbi():
    from .BitbucketInterface import BitbucketInterface
    return BitbucketInterface()

j.base.loader.makeAvailable(j, 'clients')

j.clients._register('bitbucket', bb)
j.clients._register('bitbucketi', bbi)
