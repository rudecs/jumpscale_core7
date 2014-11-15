from JumpScale import j

from .Bitbucket import Bitbucket
from .BitbucketConfigManagement import BitbucketConfigManagement
from .BitbucketInterface import BitbucketInterface

j.base.loader.makeAvailable(j, 'clients')

j.clients.bitbucket=Bitbucket()
j.clients.bitbucket._config=BitbucketConfigManagement()
j.clients.bitbucketi=BitbucketInterface()
