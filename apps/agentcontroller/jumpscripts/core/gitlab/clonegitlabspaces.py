
from JumpScale import j
from JumpScale.baselib import gitlab
from JumpScale.baselib import git

descr = """
Clone/Update gitlab user spaces
"""

organization = "jumpscale"
name = "clonegitlabspaces"
author = "hamdy.farag@codescalers.com"
license = "bsd"
version = "1.0"
async=True
roles = []
log=False


def action(username):
    print "Cloning gitlab spaces for user %s " % username
    print "**********************************************"
    client = j.clients.gitlab.get()
    projects = client.getUserSpaces(username)
    for p in projects:
        web_url = p.web_url.split('//')
        credentials = "%s:%s" % (client.login, client.passwd)
        web_url.insert(1, '//%s@' % credentials)
        web_url = ''.join(web_url)
        basedir = "/opt/jumpscale7/apps/portals/main/base/%s" % p.name
        repo = j.clients.git.getClient(basedir=basedir, remoteUrl=web_url)
        repo.fetch()

if __name__ == '__name__':
    action()