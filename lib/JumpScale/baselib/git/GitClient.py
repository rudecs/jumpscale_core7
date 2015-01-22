from JumpScale import j

class GitClient(object):

    def __init__(self, baseDir, remoteUrl, branchName='master', cleanDir=False,login="",passwd=""):
        self.baseDir = baseDir
        self.remoteUrl = remoteUrl
        self.branchName = branchName
        self.cleanDir = cleanDir
        self.login=login
        self.passwd=passwd
        self._repo = None

        if cleanDir:
            j.system.fs.removeDirTree(baseDir)
            j.system.fs.createDir(baseDir)
            self._clone()

        if branchName != 'master':
            self.switchBranch(branchName)

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

    def _clone(self):
        # Load git when we absolutly need it cause it does not work in gevent mode
        import git
        self._repo = git.Repo.clone_from(self.remoteUrl, self.baseDir)

    def switchBranch(self, branchName):
        self.repo.git.checkout(branchName)

    def getModifiedFiles(self):
        result={}
        result["D"]=[]
        result["N"]=[]
        result["M"]=[]
        result["R"]=[]

        cmd="cd %s;git status --porcelain"%self.baseDir
        rc,out=j.system.process.execute(cmd)
        for item in out.split("\n"):
            if item.strip()=="":
                continue
            item2=item.split(" ",1)[1]
            result["N"].append(item2)
        
        for diff in self.repo.index.diff(None):
            path=diff.a_blob.path
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
        cmd='cd %s;git add -A :/'%self.baseDir
        j.system.process.execute(cmd)
        # result=self.getModifiedFiles()
        # self.removeFiles(result["D"])
        # self.addFiles(result["N"])

    def addFiles(self, files=[]):
        if files!=[]:
            self.repo.index.add(files)

    def removeFiles(self, files=[]):
        if files!=[]:
            self.repo.index.remove(files)

    def pull(self):
        self.repo.git.pull()

    def fetch(self):
        self.repo.git.fetch()

    def commit(self, message='',addremove=True):
        if addremove:
            self.addRemoveFiles()
        self.repo.index.commit(message)

    def push(self,force=False):
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
            linesExisting = inn.split('\n')
            linesout = []
            for line in linesExisting:
                if line.strip():
                    linesout.append(line)
            for line in lines:
                if line not in linesExisting and line.strip():
                    linesout.append(line)
            out = '\n'.join(linesout)
            if out.strip() != inn.strip():
                j.system.fs.writeFile(ignorefilepath, out)
