

from JumpScale.core.baseclasses import BaseEnumeration

class AppStatusType(BaseEnumeration):
    """Application status"""

    def __repr__(self):
        return str(self)

AppStatusType.registerItem('running')
AppStatusType.registerItem('halted')
AppStatusType.registerItem('debug')
AppStatusType.registerItem('unknown')
AppStatusType.registerItem('init')
AppStatusType.finishItemRegistration()
