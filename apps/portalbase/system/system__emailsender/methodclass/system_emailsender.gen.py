from JumpScale import j

class system_emailsender(j.code.classGetBase()):
    """
    Email sender
    
    """
    def __init__(self):
        
        self._te={}
        self.actorname="emailsender"
        self.appname="system"
        #system_emailsender_osis.__init__(self)
    

        pass

    def send(self, sender_name, sender_email, receiver_email, subject, body, smtp_key, **kwargs):
        """
        param:sender_name Sender full name
        param:sender_email Sender email
        param:receiver_email Receiver email.
        param:subject Email subject
        param:body Email body
        param:smtp_key Email body
        result str
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method send")
    
