from JumpScale import j

class system_usermanager(j.code.classGetBase()):

    """
    register a user (can be done by user itself, no existing key or login/passwd is needed)
    
    """

    def __init__(self):

        self._te = {}
        self.actorname = "usermanager"
        self.appname = "system"
        self.osiscl = j.core.portal.active.osis
        self.modelUser = j.core.osis.getClientForCategory(self.osiscl, 'system', 'user')

    def _authSelf(self,user,kwargs):
        ctx=kwargs["ctx"]
        if not user==ctx.env['beaker.session']["user"]:
            raise RuntimeError("Authentication Error")

    def authenticate(self, name, secret, **args):
        """
        param:name name
        param:secret md5 or passwd
        result str 
        
        """
        self._authSelf(name,args)
        if not self.userexists(name):
            return False
        user=self.modelUser.get("%s_%s"%(j.application.whoAmI.gid,name))

        if user.authkey=="":
            user.authkey=j.tools.hash.md5_string(j.base.idgenerator.generateGUID())
            self.modelUser.set(user)

        if user.passwd.strip() == str(secret).strip():
            return user.authkey
        if j.tools.hash.md5_string(secret) == user.passwd:
            return user.authkey
        result = False
        return result

    def userget(self, name, **kwargs):
        """
        get a user
        param:name name of user
        """
        return self.modelUser.get("%s_%s"%(j.application.whoAmI.gid,name))

    def usergroupsget(self, user, **args):
        """
        return list of groups in which user is member of
        param:user name of user
        result list(str) 
        
        """
        raise NotImplementedError("not implemented method getusergroups")
        usermanager = j.apps.system.usermanager
        user = self._userGet(user)

        if user == None:
            # did not find user
            result = []
        else:
            # print "usergroups:%s" % user.groups
            result = user.groups

        return result

    def groupadduser(self, group, user, **args):
        """
        add user to group
        param:group name of group
        param:user name of user
        result bool 
        
        """
        # put your code here to implement this method
        raise NotImplementedError("not implemented method groupadduser")

    def groupcreate(self, name, groups, **args):
        """
        create a group
        param:name name of group
        param:groups comma separated list of groups this group belongs to
        result bool 
        
        """
        # put your code here to implement this method
        raise NotImplementedError("not implemented method groupcreate")

    def groupdeluser(self, group, user, **args):
        """
        remove user from group
        param:group name of group
        param:user name of user
        result bool 
        
        """
        # put your code here to implement this method
        raise NotImplementedError("not implemented method groupdeluser")

    def usercreate(self, name, passwd, key, groups, emails, userid, reference, remarks, config, **args):
        """
        create a user
        param:name name of user
        param:passwd passwd
        param:key specific key can be empty
        param:groups comma separated list of groups this user belongs to
        param:emails comma separated list of email addresses
        param:userid optional user id; leave 0 when not used; when entered will update existing record
        param:reference reference as used in other application using this API (optional)
        param:remarks free to be used field by client
        param:config free to be used field to store config information e.g. in json or xml format
        result bool 
        
        """
        groups = groups.split(",")
        emails = emails.split(",")
        if userid == 0:
            userid = None
        else:
            userid = userid
        result = j.apps.system.usermanager.extensions.usermanager.usercreate(name=name, passwd=passwd, groups=groups, emails=emails, userid=userid)
        return result

    def userexists(self, name, **args):
        """
        param:name name
        result bool 
        
        """
        return self.modelUser.exists("%s_%s"%(j.application.whoAmI.gid,name))

    def userregister(self, name, passwd, emails, reference, remarks, config, **args):
        """
        param:name name of user
        param:passwd chosen passwd (will be stored hashed in DB)
        param:emails comma separated list of email addresses
        param:reference reference as used in other application using this API (optional)
        param:remarks free to be used field by client
        param:config free to be used field to store config information e.g. in json or xml format
        result bool 
        
        """
        # put your code here to implement this method
        raise NotImplementedError("not implemented method userregister")
