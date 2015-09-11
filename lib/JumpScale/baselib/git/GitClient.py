from JumpScale import j


class GitClient(object):

    def __init__(self, baseDir): # NOQA
        self._repo = None
        if not j.system.fs.exists(path=baseDir):
            j.events.inputerror_critical("git repo on %s not found." % baseDir)

        # split path to find parts
        baseDir = baseDir.replace("\\", "/") # NOQA
        if baseDir.find("/code/") == -1:
            j.events.inputerror_critical(
                "jumpscale code management always requires path in form of $somewhere/code/$type/$account/$reponame")
        base = baseDir.split("/code/", 1)[1]

        if base.count("/") != 2:
            j.events.inputerror_critical(
                "jumpscale code management always requires path in form of $somewhere/code/$type/$account/$reponame")

        self.type, self.account, self.name = base.split("/")

        self.baseDir = baseDir

        if len(self.repo.remotes) != 1:
            j.events.inputerror_critical("git repo on %s is corrupt could not find remote url" % baseDir)

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return self.__repr__

    @property
    def remoteUrl(self):
        return self.repo.remotes[0].url

    @property
    def branchName(self):
        return self.repo.git.rev_parse('HEAD', abbrev_ref=True)

    @property
    def repo(self):
        # Load git when we absolutly need it cause it does not work in gevent mode
        import git
        if not self._repo:
            j.system.process.execute("git config --global http.sslVerify false")
            if not j.system.fs.exists(self.baseDir):
                self._clone()
            else:
                self._repo = git.Repo(self.baseDir)
        return self._repo

    def init(self):
        self.repo

    def switchBranch(self, branchName, create=True): # NOQA
        if create:
            import git
            try:
                self.repo.git.branch(branchName)
            except git.GitCommandError:
                # probably branch exists.
                pass
        self.repo.git.checkout(branchName)

    def getModifiedFiles(self):
        result = {}
        result["D"] = []
        result["N"] = []
        result["M"] = []
        result["R"] = []

        cmd = "cd %s;git status --porcelain" % self.baseDir
        rc, out = j.system.process.execute(cmd)
        for item in out.split("\n"):
            item = item.strip()
            if item == '':
                continue
            state, _, _file = item.partition(" ")
            if state == '??':
                result["N"].append(_file)

        for diff in self.repo.index.diff(None):
            path = diff.a_blob.path
            if diff.deleted_file:
                result["D"].append(path)
            elif diff.new_file:
                result["N"].append(path)
            elif diff.renamed:
                result["R"].append(path)
            else:
                result["M"].append(path)
        return result

    def addRemoveFiles(self):
        cmd = 'cd %s;git add -A :/' % self.baseDir
        j.system.process.execute(cmd)
        # result=self.getModifiedFiles()
        # self.removeFiles(result["D"])
        # self.addFiles(result["N"])

    def addFiles(self, files=[]):
        if files != []:
            self.repo.index.add(files)

    def removeFiles(self, files=[]):
        if files != []:
            self.repo.index.remove(files)

    def pull(self):
        self.repo.git.pull()

    def fetch(self):
        self.repo.git.fetch()

    def commit(self, message='', addremove=True):
        if addremove:
            self.addRemoveFiles()
        self.repo.index.commit(message)

    def push(self, force=False):
        if force:
            self.repo.git.push('-f')
        else:
            self.repo.git.push('--all')

    def getUntrackedFiles(self):
        return self.repo.untracked_files

    def patchGitignore(self):
        gitignore = '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]

# C extensions
*.so

# Distribution / packaging
.Python
develop-eggs/
eggs/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
.tox/
.coverage
.cache
nosetests.xml
coverage.xml

# Translations
*.mo

# Mr Developer
.mr.developer.cfg
.project
.pydevproject

# Rope
.ropeproject

# Django stuff:
*.log
*.pot

# Sphinx documentation
docs/_build/
'''
        ignorefilepath = j.system.fs.joinPaths(self.baseDir, '.gitignore')
        if not j.system.fs.exists(ignorefilepath):
            j.system.fs.writeFile(ignorefilepath, gitignore)
        else:
            lines = gitignore.split('\n')
            inn = j.system.fs.fileGetContents(ignorefilepath)
            lines = inn.split('\n')
            linesout = []
            for line in lines:
                if line.strip():
                    linesout.append(line)
            for line in lines:
                if line not in lines and line.strip():
                    linesout.append(line)
            out = '\n'.join(linesout)
            if out.strip() != inn.strip():
                j.system.fs.writeFile(ignorefilepath, out)
