from JumpScale import j
import JumpScale.grid.serverbase
from .OSISFactory import OSISFactory, OSISClientFactory
import JumpScale.baselib.hrd
import JumpScale.baselib.key_value_store
j.base.loader.makeAvailable(j, 'core')
j.base.loader.makeAvailable(j, 'clients')
j.core.osis = OSISFactory()
j.clients.osis = OSISClientFactory()
