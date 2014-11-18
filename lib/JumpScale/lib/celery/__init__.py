from JumpScale import j

from .CeleryFactory import *

j.base.loader.makeAvailable(j, 'clients')

j.clients.celery=CeleryFactory()
