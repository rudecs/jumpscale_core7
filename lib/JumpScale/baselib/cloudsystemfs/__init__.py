from JumpScale import j

from .CloudSystemFS import CloudSystemFS

j.base.loader.makeAvailable(j, 'cloud.system')

j.cloud.system.fs=CloudSystemFS()

