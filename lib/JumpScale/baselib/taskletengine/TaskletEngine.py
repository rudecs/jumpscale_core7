import sys
from JumpScale import j
import random
import imp

class InvalidTaskletName(ValueError):
    def __init__(self, name):
        ValueError.__init__(self, "Invalid tasklet name %s" % name)


class InvalidTaskletFunction(RuntimeError):
    def __init__(self, name, path):
        RuntimeError.__init__(self,
                              'Function %s in %s doesn\'t match required '
                              'argument specification' % (name, path))


class TaskletEngineFactory():
    def get(self, path):
        """
        """
        return TaskletEngine(path)

    def getGroup(self, path=""):
        """
        tasklets are grouped per subdir of directory, each name of subdir will become a taskletengine
        """
        return TaskletEngineGroup(path)


class Tasklet:
    def __init__(self):
        self.name = ""
        self.taskletsStepname = ""
        self.taskletsStepid = ""
        self.priority = ""
        self.module = None
        self.path = ""
        self.groupname = ""

    def checkExecute(self, q, i, params, service, tags):
        if j.basetype.dictionary.check(params):
            params = j.core.params.get(params)
        else:
            if not j.core.params.isParams(params):
                raise RuntimeError("Params need to be a params object, cannot execute tasklet: %s" % self.path)
        if not hasattr(self.module, 'match') or self.module.match(j, i, params, service, tags, self):
            params = self.module.main(q, i, params, service, tags, self)
        return params

    def checkExecuteV2(self, args, params, tags):
        try:
            if not hasattr(self.module, 'match') or self.module.match(j, args, params, tags, self):
                params = self.module.main(j, args, params, tags, self)
        except:
            print(self.module)
            import traceback
            traceback.print_exc()
            raise
        return params

    def checkExecute4method(self, args={}, params={}, actor=None, tags=None):
        if tags != None:
            if j.basetype.string.check(tags):
                tags = j.core.tags.getObject(tags)

        args = j.core.params.get(args)

        if not hasattr(self.module, 'match') or self.module.match(j, args, params, actor, tags, self):
            params = self.module.main(j, args, params, actor, tags, self)

        return params

    def __repr__(self):
        s = "%s %s__%s priority:%s name:%s" % (self.path, self.taskletsStepid, self.taskletsStepname, self.priority, self.name)
        return s


class TaskletEngineGroup():
    def __init__(self, path=""):
        self.taskletEngines = {}
        if path!="":
            self.addTasklets(path)

    def addTasklets(self, path):
        taskletdirs = j.system.fs.listDirsInDir(path, False, True)
        nr=0
        for taskletgroupname in taskletdirs:
            # print "####%s######"%taskletgroupname
            self.taskletEngines[taskletgroupname.lower().strip()] = TaskletEngine(j.system.fs.joinPaths(path, taskletgroupname))

    def hasGroup(self, name):
        """
        @param name always needs to be lowercase
        """
        return name in self.taskletEngines

    def execute(self, groupname, params, service=None, tags=None):
        """
        @param groupname always needs to be lowercase
        """
        if groupname in self.taskletEngines:
            return self.taskletEngines[groupname].execute(params, service, tags)
        else:
            raise RuntimeError("Cannot find groupname: %s in tasklets" % groupname)

    def executeV2(self, groupname, **args):
        """
        @param groupname always needs to be lowercase
        """
        if groupname in self.taskletEngines:
            return self.taskletEngines[groupname].executeV2(**args)
        else:
            raise RuntimeError("Cannot find groupname: %s in tasklets" % groupname)


class TaskletEngine():
    def __init__(self, path):
        """
        @param path from which tasklets will be loaded
        """
        self.tasklets = []
        self.path = path
        self._loadTasklets(path)

    def _loadTasklets(self, path):
        """
        load tasklet steps & _init.py for 1 specific group of tasklets
        """
        j.logger.log("load tasklets in %s" % (path), 6)
        # now load tasklet steps
        items = self._getDirItemsNaturalSorted(path, "_", True, True)
        if items == []:
            # no steps found
            items = [[0, "", path]]

        for prio, name, path2 in items:
            if name != "":
                path2 = j.system.fs.joinPaths(path, "%s_%s" % (prio, name))
            self._loadTaskletsFromStep(prio, name, path2)

    def _getDirItemsNaturalSorted(self, path, separator="_", strict=False, dirs=False):
        if dirs:
            items = j.system.fs.listDirsInDir(path, recursive=False)
        else:
            items = j.system.fs.listFilesInDir(path, recursive=False)
        prios = {}
        for item in items:
            dirName = j.system.fs.getBaseName(item)
            if not dirName.endswith(".py") and not dirs:
                continue
            if not dirName.startswith("_") and not dirName.startswith("."):
                splitted = dirName.split(separator)
                if not strict:
                    if not splitted:
                        prio = 5
                        name = item
                    else:
                        prioString = splitted[0]
                        if not prioString.isdigit():
                            raise InvalidTaskletName(dirName)
                        prio = int(prioString)
                        name = separator.join(splitted[1:])
                else:
                    if len(splitted) > 1:
                        prioString = splitted[0]
                        if not prioString.isdigit():
                            raise InvalidTaskletName(dirName)
                        prio = int(prioString)
                        name = separator.join(splitted[1:])
                    else:
                        raise InvalidTaskletName(dirName)

                path2 = "%s%s%s" % (prio, separator, name)
                if prio in prios:
                    prios[prio].append([name, path2])
                else:
                    prios[prio] = [[name, path2]]
        prios2 = list(prios.keys())
        prios2.sort()
        result = []
        for prio in prios2:
            for name, item in prios[prio]:
                result.append([prio, name, item])
        return result

    def _loadTaskletsFromStep(self, stepid, taskletstepname, path):
        items = self._getDirItemsNaturalSorted(path)
        for prio, name, item in items:
            ppath = j.system.fs.joinPaths(path, item)
            j.logger.log("Load tasklet %s" % ppath)
            if j.system.fs.parsePath(ppath)[2].lower() == "py":
                tasklet = Tasklet()
                tasklet.name = name.replace(".py", "")
                tasklet.taskletsStepname = taskletstepname
                tasklet.taskletsStepid = stepid
                tasklet.priority = prio
                tasklet.module = self._loadModule(ppath)
                tasklet.path = ppath
                self.tasklets.append(tasklet)

    def reloadTasklet(self, tasklet):
        tasklet.module = self._loadModule(tasklet.path)

    def execute(self, params, service=None, tags=None):
        """
        @param params is params object like from j.core.params.get() or a dict
        @param service is an object which want to give to the tasklets, it will also be called service there
        """
        # params are of type j.core.params.get() !!!
        if len(self.tasklets) == 0:
            params.result = None

        if j.basetype.string.check(tags):
            tags = j.core.tags.getObject(tags)
        else:
            tags = tags

        if "result" not in params:
            params.result = None

        for tasklet in self.tasklets:
            if params.get('stop') is True:
                return params.result
            if params.get('skipstep') is not True:
                params = tasklet.checkExecute(j, i, params, service, tags)

        return params

    def executeV2(self, **args):
        if len(self.tasklets) == 0:
            return None

        if "tags" in args:
            if j.basetype.string.check(args["tags"]):
                tags = j.core.tags.getObject(args["tags"])
            else:
                tags = args["tags"]
        else:
            tags = None

        args = j.core.params.get(args)

        params = j.core.params.get({})
        params.result = None

        for tasklet in self.tasklets:
            if params.get('stop') is True:
                return params.result
            if params.get('skipstep') is not True:
                params = tasklet.checkExecuteV2(args, params, tags)

        return params.result

    def execute4method(self, args={}, params={}, actor=None, tags=None):
        if len(self.tasklets) == 0:
            params.result = None

        if j.basetype.dictionary.check(params):
            params = j.core.params.get(params)
        else:
            if not j.core.params.isParams(params):
                raise RuntimeError("Params need to be a params object, cannot execute tasklet: %s" % self.path)

        if 'result' not in params:
            params.result = None
            # raise RuntimeError("tasklet:%s did not return a params.result"%self)

        for tasklet in self.tasklets:
            if params.get('stop') is True:
                return params
            if params.get('skipstep') is not True:
                params = tasklet.checkExecute4method(args, params, actor, tags)

        return params.result

    def _loadModule(self, path):
        '''Load the Python module from disk using a random name'''
        j.logger.log('Loading tasklet module %s' % path, 7)
        # Random name -> name in sys.modules

        def generate_module_name():
            '''Generate a random unused module name'''
            return '_tasklet_module_%d' % random.randint(0, sys.maxsize)
        modname = generate_module_name()
        while modname in sys.modules:
            modname = generate_module_name()

        module = imp.load_source(modname, path)
        return module
