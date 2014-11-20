
import cStringIO
import os

import sys
import zipfile

from JumpScale import j
import JumpScale.baselib.inifile
from JumpScale.core.extensions.PMExtensionsGroup import PMExtensionsGroup
from JumpScale.core.extensions.PMExtension import PMExtension, EggPMExtension

HOOKED_EXTENSION_DIR = dict()


#SYSTEM_EXTENSIONS = list() #list of all known extension
#HOOK_POINTS = dict()  #dict between PMExtensions and its location e.g. q.

def find_eggs(path):
    """
    Helper for egg loader functions

    @param path: path to find the eggs on
    @type path: string
    @return: a list of eggs
    @rtype: list
    """

    eggs = None

    try:
        import pkg_resources
        eggs, errors = pkg_resources.working_set.find_plugins(
            pkg_resources.Environment([path])
        )
    except:
        pass
    return eggs


class jumpscaleZipFile(zipfile.ZipFile):
    """Extends the Python 2.5 zipfile ZipFile class to add a Python 2.6 like
    open method that returns a file pointer"""
    def open(self, name, mode='r'):
        if mode != 'r':
            raise RuntimeError("Only read-only file access supported")

        content = self.read(name)
        return cStringIO.StringIO(content)


class ExtensionFactory(object):
    """Simple factory baseclass for BasePMExtension objects"""
    def build(self, extensionPath, moduleName, className, pmExtensionName):
        """
        Create a new BasePMExtensions object

        @param extensionPath: the extension root (dirname of the extension.cfg file)
        @type extensionPath: string
        @param moduleName: name of the module containing the root class of this extension
        @type moduleName: string
        @param className: name of the root class of this extension
        @type className: string
        @param pmExtensionName: name used to expose class under q.[one or more extensionsgroup's].[pmExtensionName]
        @type pmExtensionName: string
        @return: a freshly instantiated extension
        @rtype: L{jumpscale.extensions.PMextension.BasePMExtension}
        """
        raise NotImplementedError


class PMExtensionFactory(ExtensionFactory):
    """Simple factory class for PMExtension objects"""
    def build(self, extensionPath, moduleName, className, pmExtensionName, qlocation=""):
        return PMExtension(extensionPath, moduleName, className, pmExtensionName, qlocation=qlocation)


class EggPMExtensionFactory(ExtensionFactory):
    """Simple factory class for EggPMExtension objects"""
    def build(self, extensionPath, moduleName, className, pmExtensionName):
        return EggPMExtension(extensionPath, moduleName, className, pmExtensionName)


class ExtensionInfoFinder(object):
    """Base class for extension info finders"""

    def __init__(self, rootDir, extensionConfigName="extension.cfg", warn_old_extensions=True):
        self.rootDir = rootDir
        self.extensionConfigName = extensionConfigName

    def find(self):
        """
        This method starts a scan for extensions and returns information about
        each found extension. Must be implemented by children.
        """
        raise NotImplementedError

    def _getHookInformation(self, inifile, path, factory):
        """
        Extract the hook information from an inifile. path and factory are
        are extra parameters to be added to each information dict.

        @param inifile: inifile that should be scanned for extension information
        @type inifile: L{jumpscale.inifile.IniFile.IniFile}
        @param path: internal extension path
        @type path: string
        @param factory: factory to create the extension described in the INI file
        @type factory: L{PMExtensionFactory}
        @return: a list of dicts containing extension information
        @rtype: list of dicts
        """
        sections = inifile.getSections()
        hookInformationList = list()
        for hookid in sorted(section for section in sections if section.startswith('hook')):
            j.logger.log('Found hook %s in %s' % (hookid, inifile, ), 7)
            # Extract the information from the section
            hookInformation = self._extractHookInformation(inifile, hookid)
            if not hookInformation:
                continue
            # Add global information
            hookInformation['extension_path'] = path
            hookInformation['extension_factory'] = factory
            hookInformationList.append(hookInformation)
        return hookInformationList

    def _extractHookInformation(self, inifile, section):
        """
        Extract hook information from an INI file section

        @param inifile: INI file containing the section with the hook information
        @type inifile: L{jumpscale.inifile.IniFile.IniFile}
        @param section: section of the INI file that contains the hook information
        @type section: string
        @return: hook information
        @rtype: dict
        """
##        if self.warn_old_extensions and self._hasOldStyleSection(inifile):
##            #This is most likely an old-style extension
##            import warnings
##            raise RuntimeError('Extension %s contains a main section in the extension.cfg file, please update it' % \
##                    dir[len(j.dirs.extensionsDir) + 1:] if dir.startswith(j.dirs.extensionsDir) else dir)
##            # Explicit None for clarity
##            return None

        qlocation = inifile.getValue(section, "qlocation")
        modulename = inifile.getValue(section, "modulename")
        classname = inifile.getValue(section, "classname")
        enabled = inifile.getBooleanValue(section, "enabled")
        if inifile.checkParam(section, "priority"):
            priority = inifile.getValue(section, "priority")
        else:
            priority = 5

        hook = {
            'qlocation': qlocation,
            'modulename': modulename,
            'classname': classname,
            'enabled': enabled,
            'hookid': section,
            'priority': priority,
        }
        return hook


class PyExtensionInfoFinder(ExtensionInfoFinder):
    """Extension info finder class for normal extensions"""

    def find(self):
        """
        Find all extensions and hooks defined in them
        """
        extension_hooks = list()
        #Find all extension names
        dirs = j.system.fs.listDirsInDir(self.rootDir, True, findDirectorySymlinks=True)
        # print "extensiondirs:%s\n"%dirs
        dirs.append(self.rootDir)
        # Use a simple PMExtensionFactory
        factory = PMExtensionFactory()

        for dir in (d for d in dirs if j.system.fs.exists(os.path.join(d, self.extensionConfigName))):
            #we found possible extension because extension.cfg file found
            if True or j._extensionpathfilter(dir):  #disabled the extensionpath filter untill we found a better solution, now too cumbersome and not documented (kds)
                # print 'Found extension in %s' % dir
                j.logger.log('Found extension in %s' % dir, 6)
                # Load extension ini file
                configfilePath = os.path.join(dir, self.extensionConfigName)
                inifile = j.tools.inifile.open(configfilePath)
                path = j.system.fs.getDirName(configfilePath)
                hooks = self._getHookInformation(inifile, path, factory)
                extension_hooks.extend(hooks)

        return extension_hooks
    
class ActorExtensionInfoFinder(ExtensionInfoFinder):
    """Extension info finder class for normal extensions"""

    def find(self):
        """
        Find all extensions and hooks defined in them
        """
        extension_hooks = list()
        #Find all extension names
        dirs = set(j.system.fs.listDirsInDir(self.rootDir, True, findDirectorySymlinks=True))
        dirs.add(self.rootDir)
        # Use a simple PMExtensionFactory
        factory = PMExtensionFactory()
        
        for d in dirs:
            configfilePath = os.path.join(d, self.extensionConfigName)
            if j.system.fs.exists(configfilePath):
                #we found possible extension because extension.cfg file found
                # Load extension ini file
                inifile = j.tools.inifile.open(configfilePath)
                path = j.system.fs.getDirName(configfilePath)
                hooks = self._getHookInformation(inifile, path, factory)
                extension_hooks.extend(hooks)
        return extension_hooks    


class EggExtensionInfoFinder(ExtensionInfoFinder):
    """Extension info finder class for egg extensions"""
    def find(self):
        """
        Find the extensions info for extensions in egg format
        """
        extension_hooks = list()
        eggs = find_eggs(self.rootDir)
        factory = EggPMExtensionFactory()
        for egg in eggs:
            # Add egg to path so other parts of jumpscale can import its contents
            eggfile = egg.location
            sys.path.append(eggfile)
            for filePointer, path in self._generateExtensionConfigFilePointers(eggfile):
                inifile = j.tools.inifile.open(filePointer)
                hooks = self._getHookInformation(inifile, path, factory)
                extension_hooks.extend(hooks)
            return extension_hooks

    def _generateExtensionConfigFilePointers(self, eggFileName):
        """
        Generate file pointers and paths for each extension config file in a egg file.

        The generated paths are the internal paths of the extensions in the
        egg file.

        Note: this is a generator! It does not return a list.

        @param eggFileName: name of the egg file
        @type eggFileName: string
        @return: generates (file pointers, path) pairs
        @rtype: generator
        """
        # Always use forward slashes in eggs
        sep = "/"
        eggFile = jumpscaleZipFile(eggFileName)
        for internalFileName in eggFile.namelist():
            parts = internalFileName.split(sep)
            if parts and parts[-1] == self.extensionConfigName:
                # construct egg path i.e.
                # /opt/qbase2/lib/jumpscale/extensions/my_extension.egg/my_first_extension/
                # This format is supported by the eggfile module
                path = sep.join([eggFileName] + parts[:-1])
                yield eggFile.open(internalFileName), path

# Change this list to add extra kinds of extensions
# Normal extensions are loaded first
##EXTENSION_INFO_FINDER_CLASSES = [PyExtensionInfoFinder, EggExtensionInfoFinder]
EXTENSION_INFO_FINDER_CLASSES = [PyExtensionInfoFinder]


class PMExtensions:
    """
    all functionality required to load all extensions
    is added as property to root group e.g. q. or a. or p. or i.
    """

    def __init__(self, hook_base_object, hook_base_name, suppressAlreadyMountedError=False):
        """
        @param rootpaths, locations for extensions
        """
        #if isinstance(hook_base_object, PMExtensionsGroup)==False or not isinstance(hook_base_object, JumpScale):
            #raise RuntimeError("Cannot init pmextensions, because hook_base_object given is not of type PMExtensionsGroup or JumpScale(q)")
        self.hook_base_object = hook_base_object
        self.hook_base_name = hook_base_name

        # If suppressAlreadyMountedError is True no exception wil be raised if
        # an extension is loaded for the second time.
        self._suppressAlreadyMountedError = suppressAlreadyMountedError

        ##self.extensionLocationCache = dict()

        #HOOK_POINTS[hook_base_name] = self
        ##self.pmExtensionsGroups={}  #dict of multiple extenionsgroups

    def load(self, extensionDir,actor=False):
        if self.hook_base_object not in HOOKED_EXTENSION_DIR:
            HOOKED_EXTENSION_DIR[self.hook_base_object] = list()

        hookedExtensionDirs = HOOKED_EXTENSION_DIR[self.hook_base_object]

        if extensionDir in hookedExtensionDirs:
            return

        if not j.system.fs.exists(extensionDir):
            j.logger.log("Extensions dir %s does not exist" % extensionDir, 4)
            hookedExtensionDirs.append(extensionDir)
            return

        if actor:
            self._extensionInfoFinders = [ActorExtensionInfoFinder(extensionDir)]
        else:
            self._extensionInfoFinders = [klass(extensionDir) for klass in EXTENSION_INFO_FINDER_CLASSES]
        hooks = list()

        for infoFinder in self._extensionInfoFinders:
            hooks.extend(infoFinder.find())

        j.logger.log('Loading jumpscale extensions from %s' % extensionDir, 7)

        # Add extensions directory to sys.path.
        sys.path.append(extensionDir)

        # Sort the order of modules to load.
        def sortHooks(hook):
            return int(hook['priority'])

        # Walk over all found extensions.
        for hook in sorted(hooks, key=sortHooks):
            self._populateExtension(hook['extension_path'], hook)

        hookedExtensionDirs.append(extensionDir)

    def _populateExtension(self, extensionPath, hookInfo):
        qlocation = hookInfo['qlocation']
        modulename = hookInfo['modulename']
        classname = hookInfo['classname']
        enabled = hookInfo['enabled']
        priority = hookInfo['priority']
        extensionFactory = hookInfo['extension_factory']

        j.logger.log('Found %s hook %s.%s to be hooked on %s with priority %s' % (
                                'enabled' if enabled else 'disabled',
                                modulename, classname,
                                qlocation, priority), 7)

        if enabled == True:
            self._hook_extension(extensionFactory, extensionPath, modulename, classname, qlocation)

        j.logger.log('Finished loading hook', 7)

    def _hook_extension(self, extensionFactory, extensionPath, modulename, classname, qlocation):
        """
        hook extension to appropriate pmExtensionsGroup
        """

        j.logger.log('Hooking %s.%s of extension in %s on %s' % (modulename, classname, extensionPath, qlocation,), 6)

        pmExtensionName = qlocation.rpartition('.')[-1]
        if qlocation[0:1] != self.hook_base_name[0]:
            return
        extension = extensionFactory.build(extensionPath, modulename, classname, pmExtensionName, qlocation)
        #print "%s %s %s" % (qlocation, modulename,classname)

        #Attach extension instance to q object at given mountpoint (qlocation)
        qlocationparts = qlocation.split('.')[1:-1]

        #look for last extensiongroup in chain, will be current
        current = self.hook_base_object  # is the object which has this class as child (e.g. q.)
        loc = "%s" % (qlocation[0:1])
        for part in qlocationparts:
            loc = "%s.%s" % (loc, part)
            if not isinstance(current, PMExtensionsGroup):
                if current.__dict__.has_key(part):
                    current = current.__dict__[part]
                    continue
                else:
                    newExtensionGroup = PMExtensionsGroup(current)
                    newExtensionGroup.pm_location = loc
                    newExtensionGroup.pm_name = part
                    setattr(current, part, newExtensionGroup)
                    current = newExtensionGroup
                    continue
            elif current.pm_existExtensionsGroup(part):
                #extension group does already exist
                current = current.pm_extensionGroups[part]
                continue
            else:
                newExtensionGroup = PMExtensionsGroup(current)
                newExtensionGroup.pm_location = loc
                newExtensionGroup.pm_name = part
                current.pm_addExtensionsGroup(newExtensionGroup)
                current = newExtensionGroup

        #Don't allow overwriting unknown attribute on same location
        if hasattr(current, pmExtensionName):
            msg = "Cannot mount %s on mountpoint %s because unknown object %s is already mounted there" % (extension, qlocation, getattr(current, pmExtensionName))
            if self._suppressAlreadyMountedError:
                raise RuntimeError(msg)
            else:
                j.errorconditionhandler.raiseBug(msg,category="extensions.init")

        if not isinstance(current, PMExtensionsGroup):
            #is not extensionsgroup, means we need to activate right away and add to right attribute
            extension.activate()
            setattr(current, pmExtensionName, extension.instance)
        else:
            current.pm_addExtension(extension)

        #else:
            #extension.activate()
            #setattr(current, pmExtensionName, extension.instance)

        # Add the mounted extension to the cache
        ##self.extensionLocationCache[qlocation] = extension
