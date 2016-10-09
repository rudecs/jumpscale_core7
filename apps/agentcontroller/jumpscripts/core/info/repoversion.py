from JumpScale import j

descr = """
This jumpscript returns repo version information
"""

category = "monitoring"
organization = "jumpscale"
author = "deboeckj@codescalers.com"
license = "bsd"
version = "1.0"
roles = []


def action(provider, account, repo):
    path = j.do.getGitReposListLocal(provider, account, repo)[repo]
    git = j.clients.git.get(path)
    data = {'version': git.getBranchOrTag(), 'hex': git.repo.head.commit.hexsha[:7], 'timestamp': git.repo.head.commit.authored_date}
    return data

if __name__ == "__main__":
    print(action('github', 'jumpscale', 'jumpscale_core7'))
