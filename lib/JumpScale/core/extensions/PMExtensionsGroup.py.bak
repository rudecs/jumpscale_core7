from JumpScale.core.extensions.PMExtension import BasePMExtension

class _ModulePlaceholder: pass

class PMExtensionsGroup(object):
    """
    Dummy class to hold extension instances
    is middle class e.g. if q.servers.rsyncserver and servers does not exist
    """
    def __init_properties__(self):
        self.pm_extensions={}    #known extenions to this class
        self.pm_parentExtensionGroup=None   #link to parent pm_pmExtensions object
        self.pm_extensionGroups={} #groups of PMExtensions (children)
        self.pm_name=""  #name of this extensiongroup
        self.pm_location=""

    def __init__(self,parentExtensionsGroup=None):
        self.__init_properties__()
        self.pm_parentExtensionGroup=parentExtensionsGroup

    def __getattribute__(self, name):
        """
        overloaded method from python itself, getattribute gets called when anyone asks for an attribute
        """
        #call getattribute from python, goal get to your _exts without getting in loop (otherwise this method would be called again)
        if name in ('__init_properties__', 'pm_extensions', 'pm_addExtensionsGroup','pm_addExtension','pm_existExtensionsGroup','pm_existExtension','pm_parentExtensionGroup','pm_extensionGroups','pm_name','pm_location'):
            return object.__getattribute__(self, name)

        if name in self.pm_extensions:
            extension = self.pm_extensions[name]
            #we can now load the extension because someone asked for it
            extension.activate()
            return extension.instance

        return object.__getattribute__(self, name)

        ##@question WHY IS THIS?
        #try:
            #tmp = object.__getattribute__(self, name)
        #except AttributeError:
            #pass
        #else:
            ##check if the attribute is the placeholder, if not return, if yes needs to be activated
            #if tmp is not _ModulePlaceholder:
                #return tmp

        ###_extensions = object.__getattribute__(self, 'pm_groupPMExtensions')

        ##check if attribute (which would be extension of PMExtensionsGroup) exists, if not should not return method or attribute
        #if name not in self.pm_extensions:
            #raise AttributeError("cannot get method or attribute '%s' which is not an extension from a extension group object" % name)

        #extension = self.pm_extensions[name]
        ##we can now load the extension because someone asked for it
        #extension.activate()
        #return extension.instance

    def pm_addExtension(self, extension):
        '''
        Register an extension as child attribute of this object
        '''
        if isinstance(extension, BasePMExtension)==False:
            raise TypeError("Parameter = BasePMExtension to pm_addExtension")
        self.pm_extensions[extension.pmExtensionName] = extension
        setattr(self, extension.pmExtensionName, _ModulePlaceholder)

    def pm_addExtensionsGroup(self, extensionsGroup):
        '''
        Register an extension as child attribute of this object
        '''
        if extensionsGroup.pm_name=="":
            raise RuntimeError("Cannot add extensiongroup if pm_name attr is empty")
        if isinstance(extensionsGroup, PMExtensionsGroup)==False:
            raise TypeError("Parameter = PMExtensionsGroup to pm_addExtensionsGroup")
        self.pm_extensionGroups[extensionsGroup.pm_name] = extensionsGroup
        setattr(self, extensionsGroup.pm_name, extensionsGroup)

    def pm_existExtensionsGroup(self,name):
        return self.pm_extensionGroups.has_key(name)

    def pm_existExtension(self,name):
        return self.pm_extensions.has_key(name)

    def __repr__(self):
        s="Extensionsgroup:\nlocation:%s\n" % self.pm_location
        for key in self.pm_extensions.keys():
            ext=self.pm_extensions[key]
            s=" extension path:%s module:%s class:%s\n" % (ext.extensionPath,ext.moduleName,ext.className)
        for key in self.pm_extensionGroups.keys():
            group=self.pm_extensionGroups[key]
            s=" extensiongroup %s location:%s\n" % (group.pm_name,group.pm_location)
        return s

    def __str__(self):
        return self.__repr__()
