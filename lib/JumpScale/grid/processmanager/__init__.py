from JumpScale import j

from .ProcessmanagerFactory import ProcessmanagerFactory

j.base.loader.makeAvailable(j, 'core')
j.core.processmanager = ProcessmanagerFactory()
