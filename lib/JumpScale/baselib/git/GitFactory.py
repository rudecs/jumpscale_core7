from .GitClient import GitClient
from JumpScale import j
import os


class GitFactory:
    def __init__(self):
        j.logger.consolelogCategories.append("git")

    def get(self, basedir):
        """
        PLEASE USE SSH, see http://gig.gitbooks.io/jumpscale/content/Howto/how_to_use_git.html for more details
        """
        return GitClient(basedir)

    def log(self, msg, category="", level=5):
        category = "git.%s" % category
        category = category.rstrip(".")
        j.logger.log(msg, category=category, level=level)

    def find(self, account=None, name=None, interactive=False, returnGitClient=False): # NOQA
        """
        walk over repo's known on system
        2 locations are checked
            ~/code
            /opt/code
        """
        if name is None:
            name = ""
        if account is None:
            account = ""

        accounts = []
        accounttofind = account

        def checkaccount(account):
            # print accounts
            # print "%s %s"%(account,accounttofind)
            if account not in accounts:
                if accounttofind.find("*") != -1:
                    if accounttofind == "*" or account.startswith(accounttofind.replace("*", "")):
                        accounts.append(account)
                elif accounttofind != "":
                    if account.lower().strip() == accounttofind.lower().strip():
                        accounts.append(account)
                else:
                    accounts.append(account)
            # print accountsunt in accounts
            return account in accounts

        def _getRepos(codeDir, account=None, name=None): # NOQA
            """
            @param interactive if interactive then will ask to select repo's out of the list
            @para returnGitClient if True will return gitclients as result

            returns (if returnGitClient)
            [[type,account,reponame,path]]

            the type today is git or github today
            all std git repo's go to git

            ```
            #example
            [['github', 'docker', 'docker-py', '/opt/code/github/docker/docker-py'],
            ['github', 'jumpscale', 'docs', '/opt/code/github/jumpscale/docs']]
            ```

            """
            repos = []
            for top in j.system.fs.listDirsInDir(codeDir, recursive=False,
                                                 dirNameOnly=True, findDirectorySymlinks=True):
                for account in j.system.fs.listDirsInDir("%s/%s" % (j.dirs.codeDir, top), recursive=False,
                                                         dirNameOnly=True, findDirectorySymlinks=True):
                    if checkaccount(account):
                        accountdir = "%s/%s/%s" % (j.dirs.codeDir, top, account)
                        if j.system.fs.exists(path="%s/.git" % accountdir):
                            raise RuntimeError("there should be no .git at %s level" % accountdir)
                        else:
                            for reponame in j.system.fs.listDirsInDir("%s/%s/%s" % (j.dirs.codeDir, top, account),
                                                                      recursive=False, dirNameOnly=True,
                                                                      findDirectorySymlinks=True):
                                repodir = "%s/%s/%s/%s" % (j.dirs.codeDir, top, account, reponame)
                                if j.system.fs.exists(path="%s/.git" % repodir):
                                    if name.find("*") != -1:
                                        if name == "*" or reponame.startswith(name.replace("*", "")):
                                            repos.append([top, account, reponame, repodir])
                                    elif name != "":
                                        if reponame.lower().strip() == name.lower().strip():
                                            repos.append([top, account, reponame, repodir])
                                    else:
                                        repos.append([top, account, reponame, repodir])
            return repos

        j.system.fs.createDir(j.system.fs.joinPaths(os.getenv("HOME"), "code"))
        repos = _getRepos(j.dirs.codeDir, account, name)
        repos += _getRepos(j.system.fs.joinPaths(os.getenv("HOME"), "code"), account, name)

        accounts.sort()

        if interactive:
            result = []
            if len(repos) > 20:
                print("Select account to choose from, too many choices.")
                accounts = j.console.askChoiceMultiple(accounts)

            repos = [item for item in repos if item[1] in accounts]

            # only ask if * in name or name not specified
            if name.find("*") == -1 or name is None:
                repos = j.console.askArrayRow(repos)

        result = []
        if returnGitClient:
            for top, account, reponame, repodir in repos:
                cl = self.get(repodir)
                result.append(cl)
        else:
            result = repos

        return result
