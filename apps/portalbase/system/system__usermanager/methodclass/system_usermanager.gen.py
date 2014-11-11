from JumpScale import j

class system_usermanager(j.code.classGetBase()):
    """
    register a user (can be done by user itself, no existing key or login/passwd is needed)
    """
    def __init__(self):
        pass
        
        self._te={}
        self.actorname="usermanager"
        self.appname="system"
        #system_usermanager_osis.__init__(self)


    def authenticate(self, name, secret, **kwargs):
        """
        authenticate and return False if not successfull
        otherwise return secret for api
        param:name name
        param:secret md5 or passwd
        result str
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method authenticate")

    def groupadduser(self, group, user, **kwargs):
        """
        add user to group
        param:group name of group
        param:user name of user
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method groupadduser")

    def groupcreate(self, name, groups, **kwargs):
        """
        create a group
        param:name name of group
        param:groups comma separated list of groups this group belongs to
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method groupcreate")

    def groupdeluser(self, group, user, **kwargs):
        """
        remove user from group
        param:group name of group
        param:user name of user
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method groupdeluser")

    def usercreate(self, name, passwd, key, groups, emails, config, userid=0, reference="''", remarks="''", **kwargs):
        """
        create a user
        param:name name of user
        param:passwd passwd
        param:key specific key can be empty
        param:groups comma separated list of groups this user belongs to
        param:emails comma separated list of email addresses
        param:userid optional user id; leave 0 when not used; when entered will update existing record default=0
        param:reference reference as used in other application using this API (optional) default=''
        param:remarks free to be used field by client default=''
        param:config free to be used field to store config information e.g. in json or xml format
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method usercreate")

    def userexists(self, name, **kwargs):
        """
        param:name name
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method userexists")

    def userget(self, name, **kwargs):
        """
        get a user
        param:name name of user
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method userget")

    def usergroupsget(self, user, **kwargs):
        """
        return list of groups in which user is member of
        param:user name of user
        result list(str)
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method usergroupsget")

    def userregister(self, name, passwd, emails, config, reference="''", remarks="''", **kwargs):
        """
        param:name name of user
        param:passwd chosen passwd (will be stored hashed in DB)
        param:emails comma separated list of email addresses
        param:reference reference as used in other application using this API (optional) default=''
        param:remarks free to be used field by client default=''
        param:config free to be used field to store config information e.g. in json or xml format
        result bool
        """
        #put your code here to implement this method
        raise NotImplementedError ("not implemented method userregister")
