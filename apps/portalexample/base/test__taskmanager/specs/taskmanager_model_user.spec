
[actor]
	"""
	is actor to manipulate JSModel user
	"""
	method:model_user_delete
		"""
		remove the model user with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
		"""
        @tasklettemplate:modeldelete
		var:id int,None,Object identifier
        var:guid str,"",unique identifier can be used as auth key  @tags: optional
		result:bool    #True if successful, False otherwise

	method:model_user_get
		"""
		get model user with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
		"""
        @tasklettemplate:modelget
		var:id int,None,Object identifier
        var:guid str,"",unique identifier can be used as auth key  @tags: optional 
        result:object

    method:model_user_new
        """
        Create a new modelobjectuser instance and return as empty.
        A new object will be created and a new id & guid generated
        """
        @tasklettemplate:modelnew
        result:object    #the JSModel object

	method:model_user_set
		"""
		Saves model user instance starting from an existing JSModel object (data is serialized as json dict if required e.g. over rest)
		"""
        @tasklettemplate:modelupdate
        var:data str,"",data is object to save
		result:bool    #True if successful, False otherwise

	method:model_user_find
		"""
		query to model user
        @todo how to query
        example: name=aname
        secret key needs to be given
		"""
        @tasklettemplate:modelfind
		var:query str,"",unique identifier can be used as auth key
		result:list    #list of list [[$id,$guid,$relevantpropertynames...]]

    method:model_user_list
        """
        list models, used by e.g. a datagrid
        """
        @tasklettemplate:modellist novalidation
        result:json   

    method:model_user_datatables
        """
        list models, used by e.g. a datagrid
        """
        @tasklettemplate:modeldatatables returnformat:jsonraw
        result:json   


    method:model_user_create
        """
        Create a new model
        """
        @tasklettemplate:create
        var:organization str,,domain
        var:name str,,
        var:emails list(str),,list email addresses
        var:groups list(str),,which groups are we linked to
        result:json
