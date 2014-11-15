[actor] @dbtype:fs
	"""
	"""
    method:userregister
        """
        register a user (can be done by user itself, no existing key or login/passwd is needed)
        """
        var:name str,,name of user
        var:passwd str,,chosen passwd (will be stored hashed in DB)
        var:emails str,,comma separated list of email addresses
        var:reference str,'',reference as used in other application using this API (optional)
        var:remarks str,'',free to be used field by client 
        var:config str,,free to be used field to store config information e.g. in json or xml format 
        result:bool    #True if successful, False otherwise

    method:userget
        """
        get a user
        """
        var:name str,,name of user

    method:usercreate
		"""
		create a user
		"""
        var:name str,,name of user
		var:passwd str,,passwd
		var:key str,,specific key can be empty #@optional
		var:groups str,,comma separated list of groups this user belongs to
		var:emails str,,comma separated list of email addresses
		var:userid int,0,optional user id; leave 0 when not used; when entered will update existing record
        var:reference str,'',reference as used in other application using this API (optional)
        var:remarks str,'',free to be used field by client 
        var:config str,,free to be used field to store config information e.g. in json or xml format 
        result:bool    #True if successful, False otherwise

    method:authenticate @noauth
		"""
        authenticate and return False if not successfull
        otherwise return secret for api
		"""
        var:name str,,name 
		var:secret str,,md5 or passwd
        #var:refresh bool,False,if True will recreate a new key otherwise will use last key created @optional
        result:str #is key to be used to e.g use the rest interface

    method:userexists
		"""
		"""
        var:name str,,name 
        result:bool


    method:groupcreate
		"""
		create a group
		"""
        var:name str,,name of group
		var:groups str,,comma separated list of groups this group belongs to
        result:bool    #True if successful, False otherwise
		
	method:groupadduser
		"""
		add user to group
		"""
        var:group str,,name of group
		var:user str,,name of user
        result:bool    #True if successful, False otherwise
	
	method:groupdeluser
		"""
		remove user from group
		"""
        var:group str,,name of group
		var:user str,,name of user
        result:bool    #True if successful, False otherwise
		
	method:usergroupsget
		"""
		return list of groups in which user is member of
		"""
		var:user str,,name of user
        result:list(str) 

