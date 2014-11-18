
import re, functools, types, inspect
from JumpScale import j



try:
    import termios
except ImportError:
    termios = None

SINGLE_ITEM_SECTION_NAME = "main"

def isValidInifileSectionName(section):
    """ Check that this section name is valid to be used in inifiles, and to be used as a python property name on a q or i object """
    return re.match("^[\w_-]+$", section)

def isValidInifileKeyName(key):
    """ Check that this key name is valid to be used in inifiles, and to be used as a python property name on a q or i object """
    return re.match("^[\w_]+$", key)

def isValidInifileValue(value):
    # It is illegal to have semicolon in inifile value
    # TODO: more checks
    return type(value) not in str or ';' not in value

class ConfigError(Exception):
    pass

def autoCast(x):
    return x

def _dialogFunctionConstruct(dialogMethod, castMethod=autoCast, hasDefault=True):
    """ This function is intended to avoid code duplication.
        The ConfigManagementItem class has a lot of functions (dialogAskString, dialogAskInteger, ...) that have similar
        functionality, but call another function on j.gui.dialog.
        The fuction on j.gui.dialog is passed as argument (dialogMethod), and with this information a new function is constructed.
        The parameter "hasDefault" defines if the constructed function should have a "default" paramter.
    """

    def funcWithoutDefault(self, name, message):
        autoFilledIn, paramValue = self._autoFillIn(name, castMethod, default=None)
        if autoFilledIn:
            return paramValue
        else:
            self.params[name] = dialogMethod(message)
            return self.params[name]

    def funcWithDefault(self, name, message, default=None):
        autoFilledIn, paramValue = self._autoFillIn(name, castMethod, default)
        if autoFilledIn:
            return paramValue
        else:
            if self.state == self.ConfigMode.REVIEW:   # The user is reviewing configuration. The original value should be proposed as default.
                if name in self.params and self.params[name]:
                    default = self.params[name]
            self.params[name] = dialogMethod(message, default)
            return self.params[name]

    if hasDefault:
        return funcWithDefault
    else:
        return funcWithoutDefault
                    

class ConfigManagementItem(object):

    class ConfigMode:
        IDLE = 0          # No action.

        ADD = 1           # interactive mode only
                          # Error if ask() is invoked on ConfigManagementItem object with non-empty params
                          # Ask function will behave fully interactively
                          # Will suggest default values or none

        CHECKCONFIG = 2   # interactive & non-interacive mode
                          # Do not show any output!
                          # Run ask() function, and validate that all params that are asked for,
                          #   effectively exist in the params dict, and that they satisfy constraints 

        REVIEW = 3        # interactive mode only
                          # Run ask function.
                          # Suggest existing values if existing value is valid
                          # Suggest default value (or none) if existing value is not valid
                          # Interactively ask for keys which are missing in params + suggest default value or none

        PARTIALADD = 4    # interactive mode only
                          # Run ask function.
                          # Behave as CHECKCONFIG for params whose value is known
                          # Behave as ADD for params whose value is not known

        SETDEFAULTS = 5   # Non-interactive mode
                          # Do not show any output or ask any question!
                          # Run ask() function and fill in the default values in the params dict
                          # If a parameter has no default, set value to None.

    class SortMethod:
        INT_ASCENDING = 1 # The parameter (defined in SORT_PARAM) should be casted to an integer value. The items should be sorted ascending based on this integer value.

        INT_DESCENDING = 2

        STRING_ASCENDING = 3 # The parameter (defined in SORT_PARAM) should be casted to a string value. The items should be sorted ascending based on this string value.

        STRING_DESCENDING = 4

    def __init__(self, configtype, itemname, params=None, load=True,
            partialadd=False, setDefaults=False, validate=True):
        """
        Construct a new ConfigManagementItem object
        If params is given, it will be populated with those params, and self.validate() will be executed
        If no params are given
            If load == True, then config will be loaded from disk
            If setDefaults == True, then default values will be loaded
            If load == False and setDefaults == False, then config will be asked interactively 
        """
        self.configtype = configtype
        self.itemname = itemname
        self.state = self.ConfigMode.IDLE
        if params:
            self.params = params
            if partialadd:
                try:
                    # Check whether configuration is complete.
                    self.validate()
                except:
                    # If not, do a partialadd
                    self.partialadd()
            else:
                self.validate()
        else:
            self.params = {}
            if setDefaults:
                self.setDefaultValues()
            elif load:
                self.load()
                if validate:
                    self.validate()
            else:
                self.add()

    def ask(self):
        """
        Smart wizard which asks user for configuration information.
        Result is a filled in self.params dictionary with simple name-value pairs
        To be implemented in subclass.
        """
        raise NotImplementedError("ConfigManagementItem.ask() must be overridden by subclass.")

    def wrappedAsk(self):
        """ Wrapper around ask function. Here we can do things such as input buffer flushing and adding newlines when running in an action """
        if termios:
            if self.state in [self.ConfigMode.ADD, self.ConfigMode.REVIEW, self.ConfigMode.PARTIALADD]:
                termios.tcflush(0, termios.TCIFLUSH)
        j.action.startOutput()
        self.dialogMessage("")
        self.ask()
        self.dialogMessage("")
        j.action.stopOutput()

    def setDefaultValues(self):
        self.state = self.ConfigMode.SETDEFAULTS
        self.wrappedAsk()
        self.state = self.ConfigMode.IDLE

    def partialadd(self):
        """
        Behaviour for PARTIALADD mode
        """
        self.state = self.ConfigMode.PARTIALADD
        try:
            self.wrappedAsk()
        except:
            raise
        finally:
            self.state = self.ConfigMode.IDLE

    def add(self):
        self.state = self.ConfigMode.ADD
        self.wrappedAsk()
        self.state = self.ConfigMode.IDLE

    def review(self):
        if not j.application.interactive:
            raise RuntimeError("Cannot review configuration of [%s]/[%s] in non-interactive mode" % (self.configtype, self.itemname))
        self.state = self.ConfigMode.REVIEW
        self.wrappedAsk()
        self.state = self.ConfigMode.IDLE

    def validate(self):
        """
        Check that configuration is consistent. This happens by dry-running the ask() method
        and detecting whether config keys are missing or not matching constraints.
        """
        self.state = self.ConfigMode.CHECKCONFIG
        try:
            self.wrappedAsk()
        except ConfigError:
            #TODO do we want to change the return type?
            raise
        finally:
            self.state = self.ConfigMode.IDLE
        return True
        
    def save(self):
        errors = []
        if not isValidInifileSectionName(self.itemname):
            errors.append("Invalid item name [%s]\n" % self.itemname)
        for k, v in self.params.items():
            if not isValidInifileKeyName(k):
                errors.append("Invalid key name item [%s] / key [%s]\n" % (self.itemname, k))
            if not isValidInifileValue(v):
                errors.append("Invalid value item [%s] / key [%s] / value [%s]\n" % (self.itemname, k, v))
        if errors:
            raise ValueError("Invalid configuration:\n%s" % "\n".join(errors))
        file = j.config.getInifile(self.configtype)
        if not file.checkSection(self.itemname):
            file.addSection(self.itemname)
        for k, v in self.params.items():
            file.setParam(self.itemname, k, v)
        file.write()

    def load(self):
        file = j.config.getInifile(self.configtype)
        if not file.checkSection(self.itemname):
            raise ConfigError("Cannot find configuration for configtype [%s] configitem [%s]" % (self.configtype, self.itemname))
        self.params = file.getSectionAsDict(self.itemname)

    def show(self):
        lines = [self.itemname]
        for k, v in self.params.items():
            lines.append("  - " + k.ljust(12) + " = " + str(v))
        j.gui.dialog.message("\n%s\n" % "\n".join(lines))

    def _autoFillIn(self, name, castMethod, default):
        """ To be used in the ask*-methods: This function will check if it's possible to automatically add the parameter.
            This is the case in following situations:
              - The item is in CHECKCONFIG state, and the parameter is in self.params.
              - The item is in PARTIALADD state, and the parameter is passed to the Add() function.
            This function will return:
              - A boolean indicating if the parameter can be filled in automatically
              - The parameter that should be filled in automatically.
        """
        if self.state == self.ConfigMode.IDLE:  # When this method is called, we should be in state ADD, CHECKCONFIG or REVIEW.
            raise RuntimeError("Should never reach here")
        if self.state == self.ConfigMode.SETDEFAULTS: # Fill in the default value.
            if default is None:
                raise ConfigError("The parameter [%s] has no default value. All parameters should have a default value in order to use this method." % name)
            self.params[name] = default
            return True, self.params[name]
        if self.state == self.ConfigMode.CHECKCONFIG:   # Don't ask anything, just check if the parameter exists.
            if not name in self.params:
                raise ConfigError("Missing parameter: [%s]" % name)
            else:
                self.params[name] = castMethod(self.params[name])
                return True, self.params[name]
        if self.state == self.ConfigMode.PARTIALADD:
            if name in self.params:
                self.params[name] = castMethod(self.params[name])
                return True, self.params[name]
        return False, None   # Can't auto-fill in.

    # The functions below are automatically created based on the function templates in _dialogFunctionConstruct().
    # The parameter hasDefault determines whether the template funcWithDefault or funcWithoutDefault is used.
    dialogAskFilePath  = _dialogFunctionConstruct(j.gui.dialog.askFilePath, hasDefault=False)
    dialogAskDirPath   = _dialogFunctionConstruct(j.gui.dialog.askDirPath, hasDefault=False)
    dialogAskString    = _dialogFunctionConstruct(j.gui.dialog.askString)
    dialogAskYesNo     = _dialogFunctionConstruct(j.gui.dialog.askYesNo, castMethod=(lambda x: str(x).lower() == 'true'))
    dialogAskPassword  = _dialogFunctionConstruct(j.gui.dialog.askPassword, hasDefault=True)
    dialogAskInteger   = _dialogFunctionConstruct(j.gui.dialog.askInteger, castMethod=int)
    dialogAskIntegers  = _dialogFunctionConstruct(j.gui.dialog.askIntegers, castMethod=(lambda x: [int(i) for i in x.strip()[1:-1].split(",")]), hasDefault=False)
    dialogAskMultiline = _dialogFunctionConstruct(j.gui.dialog.askMultiline)
    
    def dialogAskChoice(self, name, message, choices, default=None):           # This is a special case: we have an additional parameter "choices"
        for choice in choices:
            if not type(choice) in str:
                raise ValueError("All choices should be strings")
        
        self.params[name] =j.gui.dialog.askChoice(message, choices, default)
        return self.params[name] 
    
    def dialogAskChoiceMultiple(self, name, message, choices, default=None):
        for choice in choices:
            if not type(choice) in str:
                raise ValueError("All choices should be strings")
        def partFunc(message, default):
            return j.gui.dialog.askChoiceMultiple(message, choices, default)
        constructedFunc = _dialogFunctionConstruct(partFunc, \
                                                   castMethod=(lambda x: [s.strip()[1:-1] for s in x.strip()[1:-1].split(",")]))
        return constructedFunc(self, name, message, default)
    
    def dialogAskDate(self, name, message, minValue=None, maxValue=None,
            selectedValue=None, format='YYYY/MM/DD', default=None):
        partFunc = functools.partial(j.gui.dialog.askDate, minValue=minValue, maxValue=maxValue, selectedValue=selectedValue, format=format)
        constructedFunc = _dialogFunctionConstruct(partFunc, hasDefault=False)
        return constructedFunc(self, message, default)
    
    def dialogMessage(self, message):
        if not self.state == self.ConfigMode.CHECKCONFIG:
            msg = j.gui.dialog.message(message)
            return msg
    
    def dialogShowProgress(self, minvalue, maxvalue, currentvalue):
        return j.gui.dialog.showProgress(minvalue, maxvalue, currentvalue)

    def dialogShowLogging(self, text):
        return j.gui.dialog.showLogging(text)



def generateGroupConfigManagementMethods(**kwargs):

    """ Generate UI-visible config management methods for Group config objects.
        (i.e. config objects which have multiple instances)
    """


    def add(self, itemname=None, params=None):
        """
        Add and configure [%(description)s].
        @param itemname: (optional) Name of the [%(description)s] to be added
        @type  itemname: string
        @param params:   (optional) Partial or full set of parameters to configure this object (e.g. to be used non-interactively), is a dict 
        @type  params:   dict
        """
        # Ask name of item to be added - check for duplicates, check for invalid inifile
        # Create new ConfigManagementItem instance and invoke ask(.) function on that item
        if itemname:   # Itemname is given as parameter...
            if itemname in self.list():  # Check if there isn't another item with this name.
                raise RuntimeError("There is already a %s with this name. Please try again." % self._DESCRIPTION)
        else:  # Itemname is not given as parameter.
            while itemname is None:  # Ask the user to enter a name. (Until he entered a valid name.)
                itemname = self._itemnameAsk()
                if not itemname:
                    j.gui.dialog.message("The name can only contain lowercase letter, numbers and underscores. Please try again.")
                if itemname in self.list():
                    j.gui.dialog.message("There is already a %s with this name. Please try again." % self._DESCRIPTION)
                    itemname = None            
        if params is not None:
            # When params are given
            #   If interactive mode: Use these params as a partial set of params. Ask the values, but populate existing values as defaults in UI.
            #   If non-interactive mode: Use these params as full set of params. If values are missing --> error
            partialadd = j.application.interactive
            item = self._ITEMCLASS(self._CONFIGTYPE, itemname, params=params, load=False, partialadd=partialadd)
        else:
            # No parameters are given, the user should answer all questions defined in the ask() method.
            item = self._ITEMCLASS(self._CONFIGTYPE, itemname, load=False)
        item.itemname=itemname
        item.save()
        if hasattr(self._ITEMCLASS, "commit") and inspect.ismethod(self._ITEMCLASS.commit):
            item.commit()  # If commit() is defined by the ItemClass, signal that configuration has been changed.

    try:
        add.__doc__ = add.__doc__ % kwargs
    except:
        pass

    def _sortConfigList(self, config):
        if not hasattr(self, '_SORT_PARAM') or not hasattr(self, '_SORT_METHOD'):
            return list(config.keys())

        def _sort(a, b):
            itemA = config[a][self._SORT_PARAM]
            itemB = config[b][self._SORT_PARAM]

            if self._SORT_METHOD == self._ITEMCLASS.SortMethod.INT_ASCENDING or \
            self._SORT_METHOD == self._ITEMCLASS.SortMethod.INT_DESCENDING:
                itemA = int(itemA)
                itemB = int(itemB)
            return cmp(itemA, itemB)

        configKeys = list(config.keys())

        reverse = (self._SORT_METHOD == self._ITEMCLASS.SortMethod.INT_DESCENDING or \
                   self._SORT_METHOD == self._ITEMCLASS.SortMethod.STRING_DESCENDING)

        configKeys.sort(cmp=_sort, reverse=reverse)
        return configKeys

    def list(self):
        """
        List all [%(description)s]s
        """
        # return list of names of ConfigManagementItem instances
        return self._sortConfigList(j.config.getConfig(self._CONFIGTYPE))

    def saveAll(self):
        for itemname in self.list():
            item = self._ITEMCLASS(self._CONFIGTYPE, itemname, load=True, validate=False)
            item.save()

    def getConfig(self, itemname=None):
        """
        Get config dictionary for a [%(description)s]
        @param itemname: (optional) Name of the [%(description)s]
        @type  itemname: string
        """
        if not itemname:
            itemname = self._itemnameSelect("Please select a %s" % self._DESCRIPTION)
        return j.config.getConfig(self._CONFIGTYPE)[itemname]


    def review(self, itemname=None):
        """
        In interactive mode: modify/review configuration of [%(description)s].
        In non-interactive mode: validate configuration of [%(description)s].
        @param itemname: (optional) Name of the [%(description)s] to be reviewed
        @type  itemname: string
        """
        # (if itemname==None) show list of items and let user choose an item
        # Invoke review(.) on that item
        if not itemname:
            itemname = self._itemnameSelect("Please select a %s" % self._DESCRIPTION)
        item = self._ITEMCLASS(self._CONFIGTYPE, itemname, load=True, validate=False)
        if j.application.interactive:
            item.review()
        else:
            item.validate()
        item.save()
        if hasattr(self._ITEMCLASS, "commit") and inspect.ismethod(self._ITEMCLASS.commit):
            item.commit()


    def show(self, itemnames=None):
        """
        Show [%(description)s] configuration.
        @param itemnames: (optional) List of [%(description)s] item names (default = all items shown)
        @type  itemnames: list of string
        """
        if itemnames is None:
            itemnames = self.list()

        for name in itemnames:
            item = self._ITEMCLASS(self._CONFIGTYPE, name, load=True)
            j.action.startOutput()
            item.show()
            j.action.stopOutput()


    def remove(self, itemname=None):
        """
        Remove [%(description)s].
        @param itemname: (optional) Name of [%(description)s]
        @type  itemname: string
        """
        # If no itemname given, show list of items and let user choose one
        # Remove ConfigManagementItem from internal list
        #
        # Remove item and remove it from the q tree
        if not itemname:
            itemname = self._itemnameSelect("Please select a %s" % self._DESCRIPTION)
        if hasattr(self._ITEMCLASS, "remove") and inspect.ismethod(self._ITEMCLASS.remove):
            item = self._ITEMCLASS(self._CONFIGTYPE, itemname, load=True)
            item.remove()
        self._itemRemove(itemname)


    def configure(self, itemname, newparams):
        """
        Reconfigure or add a [%(description)s] non-interactively.
        @param itemname:  Name of [%(description)s]
        @type  itemname:  string
        @param newparams: Complete or partial set of new configuration settings [%(keys)s]
        @type  newparams: dict of (string, value) 
        """
        existingItem = (itemname in self.list())
        if not existingItem:
            raise Exception("No existing item found. (type: [%s], name: [%s]) If you want to add a new item, please use the add() method." % (self._CONFIGTYPE, itemname))
        if not newparams:
            item = self._ITEMCLASS(self._CONFIGTYPE, itemname, load=True)
            item.validate()
            return   # Nothing changed.
        else:
            item = self._ITEMCLASS(self._CONFIGTYPE, itemname, load=True)
            for (key, value) in newparams.items():
                item.params[key] = value
            item.validate()
            item.save()
            if hasattr(self._ITEMCLASS, "commit") and inspect.ismethod(self._ITEMCLASS.commit):
                item.commit()


    return {"add": add, "list": list, "getConfig": getConfig, "review": review, "show": show, "remove": remove, "configure": configure, "_sortConfigList":_sortConfigList, "saveAll": saveAll}



class GroupConfigManagement(object):
    """
    Classes inheriting from GroupConfigManagement will be put on i tree.
    Serves for configuration of a collection of ConfigManagementItem classes.
    """

    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):

            try:
                GroupConfigManagement
            except NameError:
                return type.__new__(cls, name, bases, attrs)

            docstringInformation = {"description" : attrs["_DESCRIPTION"] }
            if "_KEYS" in attrs:
                docstringInformation['keys'] = attrs["_KEYS"]
            else:
                docstringInformation['keys'] = ""
                
            if hasattr(attrs["_ITEMCLASS"], "retrieve") and inspect.ismethod(attrs["_ITEMCLASS"].retrieve):
                def find(self, itemname=None):
                    """
                    Find configured [%(description)s]
                    """
                    if not itemname:
                        itemname = self._itemnameSelect("Please select a %s" % self._DESCRIPTION)
                    return self._ITEMCLASS(self._CONFIGTYPE, itemname, load=True).retrieve()
                find.__doc__ = find.__doc__ % docstringInformation
                attrs['find'] = find

            myMethods = generateGroupConfigManagementMethods(**docstringInformation)
            attrs.update(myMethods)

            return type.__new__(cls, name, bases, attrs)

    def _itemnameSelect(self, message):
        if len(self.list()) == 0:
            raise ValueError("No configured items of type [%s]" % self._DESCRIPTION)
        return j.gui.dialog.askChoice(message, self.list())

    def _itemnameAsk(self):
        # Ask itemname to user.
        # If self._itemdescription has been defined, use it to make a useful question
        # Check that the name is compatible with the persistency technology (e.g. inifile sectionname)
        name = j.gui.dialog.askString("Please enter a name for the %s" % self._DESCRIPTION)
        if isValidInifileSectionName(name):
            return name
        else:
            return None

    def _itemRemove(self, itemname):
        # Remove item from configuration file
        inifile = j.config.getInifile(self._CONFIGTYPE)
        inifile.removeSection(itemname)
        inifile.write()





def generateSingleConfigManagementMethods(**kwargs):

    """ Generate UI-visible config management methods for Single config objects.
        (i.e. config objects which have only one 'main' section and no other sections)
    """
    
    def review(self):
        """
        In interactive mode: modify/review configuration of [%(description)s].
        In non-interactive mode: validate configuration of [%(description)s].
        """
        if self._checkConfigItemExists():
            item = self._ITEMCLASS(self._CONFIGTYPE, SINGLE_ITEM_SECTION_NAME, load=True)
            if j.application.interactive:
                item.review()
            else:
                item.validate()
        else:
            item = self._ITEMCLASS(self._CONFIGTYPE, SINGLE_ITEM_SECTION_NAME, load=False)
        item.save()
        if hasattr(self._ITEMCLASS, "commit") and inspect.ismethod(self._ITEMCLASS.commit):
            item.commit()

    review.__doc__ = review.__doc__ % kwargs

    def show(self):
        """
        Show [%(description)s] configuration.
        """
        item = self._ITEMCLASS(self._CONFIGTYPE, SINGLE_ITEM_SECTION_NAME, load=True)
        j.action.startOutput()
        item.show()
        j.action.stopOutput()

    show.__doc__ = show.__doc__ % kwargs

    def setDefaultValues(self):
        """
        Reset the default values of [%(description)s] configuration.
        """
        item = self._ITEMCLASS(self._CONFIGTYPE, SINGLE_ITEM_SECTION_NAME, load=False, setDefaults=True)
        item.save()

    setDefaultValues.__doc__ = setDefaultValues.__doc__ % kwargs

    def configure(self, newparams):
        """
        Reconfigure a [%(description)s] non-interactively.
        @param newparams: New configuration settings
        @type  newparams: dict of (string, value)
        """

        if newparams is None:
            raise ConfigError("configure called with None parameters")

        if not self._checkConfigItemExists():
            # Completely new [main] section
            item = self._ITEMCLASS(self._CONFIGTYPE, SINGLE_ITEM_SECTION_NAME, newparams)
        else:
            # Existing [main] section which we potentially modify
            item = self._ITEMCLASS(self._CONFIGTYPE, SINGLE_ITEM_SECTION_NAME, load=True)
            for (key, value) in newparams.items():
                item.params[key] = value
            item.validate()

        item.save()

        if hasattr(self._ITEMCLASS, "commit") and inspect.ismethod(self._ITEMCLASS.commit):
            item.commit()

    configure.__doc__ = configure.__doc__ % kwargs

    def getConfig(self, itemname=None):
        """
        Get config dictionary for [%(description)s]
        """
        return j.config.getConfig(self._CONFIGTYPE)[SINGLE_ITEM_SECTION_NAME]

    getConfig.__doc__ = getConfig.__doc__ % kwargs
    return {"review": review, "show": show, "configure": configure, "setDefaultValues": setDefaultValues, "getConfig": getConfig}


class SingleConfigManagement(object):
    """
    Classes inheriting from ConfigManagement will be put on i tree.
    Serves for configuration of a single ConfigManagementItem class.
    """
   
    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):

            try:
                SingleConfigManagement
            except NameError:
                return type.__new__(cls, name, bases, attrs)

            docstringInformation = {"description" : attrs["_DESCRIPTION"]}

            myMethods = generateSingleConfigManagementMethods(**docstringInformation)
            attrs.update(myMethods)

            return type.__new__(cls, name, bases, attrs)

    def _checkConfigItemExists(self):
        if not (self._CONFIGTYPE in j.config.list()):
            return False
        elif len(j.config.getConfig(self._CONFIGTYPE)) == 0:
            return False
        else:
            return True
