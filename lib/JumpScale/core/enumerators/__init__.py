from JumpScale import j

import JumpScale.core.system

##__all__ = ['PlatformType', 'AppStatusType', 'ErrorconditionLevel', 'LogLevel', 'MessageType', 'ActionStatus', 'SeverityType', 'AppStatusType', 'JobStatusType', 'REST']
##from JumpScale.core.enumerators.SeverityType import SeverityType
from JumpScale.core.enumerators.AppStatusType import AppStatusType
# from JumpScale.core.enumerators.LogLevel import LogLevel
from JumpScale.core.enumerators.MessageType import MessageType

class Empty():
	pass

j.enumerators=Empty()

j.enumerators.AppStatusType=AppStatusType
# j.enumerators.LogLevel=LogLevel
j.enumerators.MessageType=MessageType


