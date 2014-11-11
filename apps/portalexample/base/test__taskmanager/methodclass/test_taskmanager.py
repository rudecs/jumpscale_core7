from JumpScale import j
from test_taskmanager_osis import test_taskmanager_osis


class test_taskmanager(test_taskmanager_osis):
    """
    task manager
    
    """
    def __init__(self):
        
        self._te={}
        self.actorname="taskmanager"
        self.appname="test"
        test_taskmanager_osis.__init__(self)
    

        pass

    def checkAvailability(self, name, **kwargs):
        """
        param:name name of user to check availability for
        result int 
        
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method checkAvailability")
    
