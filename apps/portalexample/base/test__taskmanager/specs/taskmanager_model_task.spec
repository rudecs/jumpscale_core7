
[actor]
	"""
	is actor to manipulate JSModel task
	"""
	method:model_task_delete
		"""
		remove the model task with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
		"""
        @tasklettemplate:modeldelete
		var:id int,None,Object identifier
        var:guid str,"",unique identifier can be used as auth key  @tags: optional
		result:bool    #True if successful, False otherwise

	method:model_task_get
		"""
		get model task with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
		"""
        @tasklettemplate:modelget
		var:id int,None,Object identifier
        var:guid str,"",unique identifier can be used as auth key  @tags: optional 
        result:object

    method:model_task_new
        """
        Create a new modelobjecttask instance and return as empty.
        A new object will be created and a new id & guid generated
        """
        @tasklettemplate:modelnew
        result:object    #the JSModel object

	method:model_task_set
		"""
		Saves model task instance starting from an existing JSModel object (data is serialized as json dict if required e.g. over rest)
		"""
        @tasklettemplate:modelupdate
        var:data str,"",data is object to save
		result:bool    #True if successful, False otherwise

	method:model_task_find
		"""
		query to model task
        @todo how to query
        example: name=aname
        secret key needs to be given
		"""
        @tasklettemplate:modelfind
		var:query str,"",unique identifier can be used as auth key
		result:list    #list of list [[$id,$guid,$relevantpropertynames...]]

    method:model_task_list
        """
        list models, used by e.g. a datagrid
        """
        @tasklettemplate:modellist novalidation
        result:json   

    method:model_task_datatables
        """
        list models, used by e.g. a datagrid
        """
        @tasklettemplate:modeldatatables returnformat:jsonraw
        result:json   


    method:model_task_create
        """
        Create a new model
        """
        @tasklettemplate:create
        var:name str,,
        var:description str,,
        var:priority int,,level 1-9 1 is most urgent
        var:project str,,link to project
        var:type str,,type comes from table tasktype and is grouped per project
        var:urgency str,,TODAY WEEK MONTH LATER
        var:taskowner str,,owner of task (user)
        var:members list(str),,list members if group
        result:json
