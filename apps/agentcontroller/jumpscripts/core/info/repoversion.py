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
    return j.clients.git.get(path).getBranchOrTag()

if __name__ == "__main__":
    print action('github', 'jumpscale', 'jumpscale_core7')