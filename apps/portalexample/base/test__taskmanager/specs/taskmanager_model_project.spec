
[actor]
	"""
	is actor to manipulate JSModel project
	"""
	method:model_project_delete
		"""
		remove the model project with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
		"""
        @tasklettemplate:modeldelete
		var:id int,None,Object identifier
        var:guid str,"",unique identifier can be used as auth key  @tags: optional
		result:bool    #True if successful, False otherwise

	method:model_project_get
		"""
		get model project with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
		"""
        @tasklettemplate:modelget
		var:id int,None,Object identifier
        var:guid str,"",unique identifier can be used as auth key  @tags: optional 
        result:object

    method:model_project_new
        """
        Create a new modelobjectproject instance and return as empty.
        A new object will be created and a new id & guid generated
        """
        @tasklettemplate:modelnew
        result:object    #the JSModel object

	method:model_project_set
		"""
		Saves model project instance starting from an existing JSModel object (data is serialized as json dict if required e.g. over rest)
		"""
        @tasklettemplate:modelupdate
        var:data str,"",data is object to save
		result:bool    #True if successful, False otherwise

	method:model_project_find
		"""
		query to model project
        @todo how to query
        example: name=aname
        secret key needs to be given
		"""
        @tasklettemplate:modelfind
		var:query str,"",unique identifier can be used as auth key
		result:list    #list of list [[$id,$guid,$relevantpropertynames...]]

    method:model_project_list
        """
        list models, used by e.g. a datagrid
        """
        @tasklettemplate:modellist novalidation
        result:json   

    method:model_project_datatables
        """
        list models, used by e.g. a datagrid
        """
        @tasklettemplate:modeldatatables returnformat:jsonraw
        result:json   


    method:model_project_create
        """
        Create a new model
        """
        @tasklettemplate:create
        var:name str,,domain
        var:descr str,,
        var:organizations list(str),,which organizations is proj linked to
        result:json
