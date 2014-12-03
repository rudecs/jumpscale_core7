
from JumpScale.core.baseclasses import BaseEnumeration



class MessageType(BaseEnumeration):
    """
    iterator for types of messages
    - logmessage
    - errorcondition, e.g. 
       - bug in application (a raised error by jumpscale)
       - cpu overloaded (detected by monitoring tasklet) 
    - testresult e.g. avgcpu over last 1h 
    - job message e.g. tells information about object
    - JSModel update message 
    - rpc message 
    more info see: 
    - http://www.jumpscale.org/display/PM/JumpScale+Messages
    - http://www.jumpscale.org/display/PM/MessageTypes
    """

    def __init__(self, level):
        self.level = level

    def __int__(self):
        return self.level
    
    def __cmp__(self, other):
        return cmp(int(self), int(other))

MessageType.registerItem('unknown', 0)
MessageType.registerItem('log', 1)
MessageType.registerItem('errorcondition', 2)
MessageType.registerItem('testresult', 3)
MessageType.registerItem('job', 4)
MessageType.registerItem('JSModel', 5)
MessageType.registerItem('rpc', 6)
#MessageType.registerItem('tlog', 7)



MessageType.finishItemRegistration()
