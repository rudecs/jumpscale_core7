from JumpScale import j

class test_taskmanager_osis(j.code.classGetBase()):
    """
    task manager
    
    """
    def __init__(self):
        self.dbmem=j.db.keyvaluestore.getMemoryStore()
        self.db=self.dbmem
        self.dbfs=j.db.keyvaluestore.getFileSystemStore(namespace="taskmanager", baseDir=None,serializers=[j.db.serializers.getSerializerType('j')])
    

        pass

    def model_group_create(self, domain, name, organizations, **kwargs):
        """
        Create a new model
        param:domain domain
        param:name 
        param:organizations which organizations is group linked to
        result json 
        
        """
        
        group = self.models.group.new()
        group.domain = domain
        group.name = name
        group.organizations = organizations
        
        return self.models.group.set(group)
                
    

    def model_group_datatables(self, **kwargs):
        """
        list models, used by e.g. a datagrid
        result json 
        
        """
        
        return self.models.group.datatables() #@todo
                    
    

    def model_group_delete(self, id, guid='', **kwargs):
        """
        remove the model group with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
        param:id Object identifier
        param:guid unique identifier can be used as auth key default=
        result bool 
        
        """
        
        return self.models.group.delete(guid=guid, id=id)
                    
    

    def model_group_find(self, query='', **kwargs):
        """
        query to model group
        @todo how to query
        example: name=aname
        secret key needs to be given
        param:query unique identifier can be used as auth key default=
        result list 
        
        """
        
        return self.models.group.find(query)            
                    
    

    def model_group_get(self, id, guid='', **kwargs):
        """
        get model group with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
        param:id Object identifier
        param:guid unique identifier can be used as auth key default=
        result object 
        
        """
        
        obj = self.models.group.get(id=id,guid=guid).obj2dict()
        obj.pop('_meta', None)
        return obj
                    
    

    def model_group_list(self, **kwargs):
        """
        list models, used by e.g. a datagrid
        result json 
        
        """
        
        return self.models.group.list()            
                    
    

    def model_group_new(self, **kwargs):
        """
        Create a new modelobjectgroup instance and return as empty.
        A new object will be created and a new id & guid generated
        result object 
        
        """
        
        return self.models.group.new()
                    
    

    def model_group_set(self, data='', **kwargs):
        """
        Saves model group instance starting from an existing JSModel object (data is serialized as json dict if required e.g. over rest)
        param:data data is object to save default=
        result bool 
        
        """
        
        return self.models.group.set(data)            
                    
    

    def model_organization_create(self, name, descr, **kwargs):
        """
        Create a new model
        param:name domain
        param:descr 
        result json 
        
        """
        
        organization = self.models.organization.new()
        organization.name = name
        organization.descr = descr
        
        return self.models.organization.set(organization)
                
    

    def model_organization_datatables(self, **kwargs):
        """
        list models, used by e.g. a datagrid
        result json 
        
        """
        
        return self.models.organization.datatables() #@todo
                    
    

    def model_organization_delete(self, id, guid='', **kwargs):
        """
        remove the model organization with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
        param:id Object identifier
        param:guid unique identifier can be used as auth key default=
        result bool 
        
        """
        
        return self.models.organization.delete(guid=guid, id=id)
                    
    

    def model_organization_find(self, query='', **kwargs):
        """
        query to model organization
        @todo how to query
        example: name=aname
        secret key needs to be given
        param:query unique identifier can be used as auth key default=
        result list 
        
        """
        
        return self.models.organization.find(query)            
                    
    

    def model_organization_get(self, id, guid='', **kwargs):
        """
        get model organization with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
        param:id Object identifier
        param:guid unique identifier can be used as auth key default=
        result object 
        
        """
        
        obj = self.models.organization.get(id=id,guid=guid).obj2dict()
        obj.pop('_meta', None)
        return obj
                    
    

    def model_organization_list(self, **kwargs):
        """
        list models, used by e.g. a datagrid
        result json 
        
        """
        
        return self.models.organization.list()            
                    
    

    def model_organization_new(self, **kwargs):
        """
        Create a new modelobjectorganization instance and return as empty.
        A new object will be created and a new id & guid generated
        result object 
        
        """
        
        return self.models.organization.new()
                    
    

    def model_organization_set(self, data='', **kwargs):
        """
        Saves model organization instance starting from an existing JSModel object (data is serialized as json dict if required e.g. over rest)
        param:data data is object to save default=
        result bool 
        
        """
        
        return self.models.organization.set(data)            
                    
    

    def model_project_create(self, name, descr, organizations, **kwargs):
        """
        Create a new model
        param:name domain
        param:descr 
        param:organizations which organizations is proj linked to
        result json 
        
        """
        
        project = self.models.project.new()
        project.name = name
        project.descr = descr
        project.organizations = organizations
        
        return self.models.project.set(project)
                
    

    def model_project_datatables(self, **kwargs):
        """
        list models, used by e.g. a datagrid
        result json 
        
        """
        
        return self.models.project.datatables() #@todo
                    
    

    def model_project_delete(self, id, guid='', **kwargs):
        """
        remove the model project with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
        param:id Object identifier
        param:guid unique identifier can be used as auth key default=
        result bool 
        
        """
        
        return self.models.project.delete(guid=guid, id=id)
                    
    

    def model_project_find(self, query='', **kwargs):
        """
        query to model project
        @todo how to query
        example: name=aname
        secret key needs to be given
        param:query unique identifier can be used as auth key default=
        result list 
        
        """
        
        return self.models.project.find(query)            
                    
    

    def model_project_get(self, id, guid='', **kwargs):
        """
        get model project with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
        param:id Object identifier
        param:guid unique identifier can be used as auth key default=
        result object 
        
        """
        
        obj = self.models.project.get(id=id,guid=guid).obj2dict()
        obj.pop('_meta', None)
        return obj
                    
    

    def model_project_list(self, **kwargs):
        """
        list models, used by e.g. a datagrid
        result json 
        
        """
        
        return self.models.project.list()            
                    
    

    def model_project_new(self, **kwargs):
        """
        Create a new modelobjectproject instance and return as empty.
        A new object will be created and a new id & guid generated
        result object 
        
        """
        
        return self.models.project.new()
                    
    

    def model_project_set(self, data='', **kwargs):
        """
        Saves model project instance starting from an existing JSModel object (data is serialized as json dict if required e.g. over rest)
        param:data data is object to save default=
        result bool 
        
        """
        
        return self.models.project.set(data)            
                    
    

    def model_task_create(self, name, description, priority, project, type, urgency, taskowner, members, **kwargs):
        """
        Create a new model
        param:name 
        param:description 
        param:priority level 1-9 1 is most urgent
        param:project link to project
        param:type type comes from table tasktype and is grouped per project
        param:urgency TODAY WEEK MONTH LATER
        param:taskowner owner of task (user)
        param:members list members if group
        result json 
        
        """
        
        task = self.models.task.new()
        task.name = name
        task.description = description
        task.priority = priority
        task.project = project
        task.type = type
        task.urgency = urgency
        task.taskowner = taskowner
        task.members = members
        
        return self.models.task.set(task)
                
    

    def model_task_datatables(self, **kwargs):
        """
        list models, used by e.g. a datagrid
        result json 
        
        """
        
        return self.models.task.datatables() #@todo
                    
    

    def model_task_delete(self, id, guid='', **kwargs):
        """
        remove the model task with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
        param:id Object identifier
        param:guid unique identifier can be used as auth key default=
        result bool 
        
        """
        
        return self.models.task.delete(guid=guid, id=id)
                    
    

    def model_task_find(self, query='', **kwargs):
        """
        query to model task
        @todo how to query
        example: name=aname
        secret key needs to be given
        param:query unique identifier can be used as auth key default=
        result list 
        
        """
        
        return self.models.task.find(query)            
                    
    

    def model_task_get(self, id, guid='', **kwargs):
        """
        get model task with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
        param:id Object identifier
        param:guid unique identifier can be used as auth key default=
        result object 
        
        """
        
        obj = self.models.task.get(id=id,guid=guid).obj2dict()
        obj.pop('_meta', None)
        return obj
                    
    

    def model_task_list(self, **kwargs):
        """
        list models, used by e.g. a datagrid
        result json 
        
        """
        
        return self.models.task.list()            
                    
    

    def model_task_new(self, **kwargs):
        """
        Create a new modelobjecttask instance and return as empty.
        A new object will be created and a new id & guid generated
        result object 
        
        """
        
        return self.models.task.new()
                    
    

    def model_task_set(self, data='', **kwargs):
        """
        Saves model task instance starting from an existing JSModel object (data is serialized as json dict if required e.g. over rest)
        param:data data is object to save default=
        result bool 
        
        """
        
        return self.models.task.set(data)            
                    
    

    def model_tasktype_create(self, name, descr, project, **kwargs):
        """
        Create a new model
        param:name domain
        param:descr 
        param:project project this is linked to
        result json 
        
        """
        
        tasktype = self.models.tasktype.new()
        tasktype.name = name
        tasktype.descr = descr
        tasktype.project = project
        
        return self.models.tasktype.set(tasktype)
                
    

    def model_tasktype_datatables(self, **kwargs):
        """
        list models, used by e.g. a datagrid
        result json 
        
        """
        
        return self.models.tasktype.datatables() #@todo
                    
    

    def model_tasktype_delete(self, id, guid='', **kwargs):
        """
        remove the model tasktype with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
        param:id Object identifier
        param:guid unique identifier can be used as auth key default=
        result bool 
        
        """
        
        return self.models.tasktype.delete(guid=guid, id=id)
                    
    

    def model_tasktype_find(self, query='', **kwargs):
        """
        query to model tasktype
        @todo how to query
        example: name=aname
        secret key needs to be given
        param:query unique identifier can be used as auth key default=
        result list 
        
        """
        
        return self.models.tasktype.find(query)            
                    
    

    def model_tasktype_get(self, id, guid='', **kwargs):
        """
        get model tasktype with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
        param:id Object identifier
        param:guid unique identifier can be used as auth key default=
        result object 
        
        """
        
        obj = self.models.tasktype.get(id=id,guid=guid).obj2dict()
        obj.pop('_meta', None)
        return obj
                    
    

    def model_tasktype_list(self, **kwargs):
        """
        list models, used by e.g. a datagrid
        result json 
        
        """
        
        return self.models.tasktype.list()            
                    
    

    def model_tasktype_new(self, **kwargs):
        """
        Create a new modelobjecttasktype instance and return as empty.
        A new object will be created and a new id & guid generated
        result object 
        
        """
        
        return self.models.tasktype.new()
                    
    

    def model_tasktype_set(self, data='', **kwargs):
        """
        Saves model tasktype instance starting from an existing JSModel object (data is serialized as json dict if required e.g. over rest)
        param:data data is object to save default=
        result bool 
        
        """
        
        return self.models.tasktype.set(data)            
                    
    

    def model_user_create(self, organization, name, emails, groups, **kwargs):
        """
        Create a new model
        param:organization domain
        param:name 
        param:emails list email addresses
        param:groups which groups are we linked to
        result json 
        
        """
        
        user = self.models.user.new()
        user.organization = organization
        user.name = name
        user.emails = emails
        user.groups = groups
        
        return self.models.user.set(user)
                
    

    def model_user_datatables(self, **kwargs):
        """
        list models, used by e.g. a datagrid
        result json 
        
        """
        
        return self.models.user.datatables() #@todo
                    
    

    def model_user_delete(self, id, guid='', **kwargs):
        """
        remove the model user with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
        param:id Object identifier
        param:guid unique identifier can be used as auth key default=
        result bool 
        
        """
        
        return self.models.user.delete(guid=guid, id=id)
                    
    

    def model_user_find(self, query='', **kwargs):
        """
        query to model user
        @todo how to query
        example: name=aname
        secret key needs to be given
        param:query unique identifier can be used as auth key default=
        result list 
        
        """
        
        return self.models.user.find(query)            
                    
    

    def model_user_get(self, id, guid='', **kwargs):
        """
        get model user with specified id and optionally guid
        if secret key is given then guid is not needed, other guid is authentication key
        param:id Object identifier
        param:guid unique identifier can be used as auth key default=
        result object 
        
        """
        
        obj = self.models.user.get(id=id,guid=guid).obj2dict()
        obj.pop('_meta', None)
        return obj
                    
    

    def model_user_list(self, **kwargs):
        """
        list models, used by e.g. a datagrid
        result json 
        
        """
        
        return self.models.user.list()            
                    
    

    def model_user_new(self, **kwargs):
        """
        Create a new modelobjectuser instance and return as empty.
        A new object will be created and a new id & guid generated
        result object 
        
        """
        
        return self.models.user.new()
                    
    

    def model_user_set(self, data='', **kwargs):
        """
        Saves model user instance starting from an existing JSModel object (data is serialized as json dict if required e.g. over rest)
        param:data data is object to save default=
        result bool 
        
        """
        
        return self.models.user.set(data)            
                    
    
