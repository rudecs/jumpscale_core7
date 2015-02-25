
from JumpScale import j
from JumpScale.baselib import gitlab
from JumpScale.baselib import git

descr = """
Clone/Update gitlab user spaces
"""

organization = "jumpscale"
name = "clonegitlabspace"
author = "hamdy.farag@codescalers.com"
license = "bsd"
version = "1.0"
async=True
roles = []
log=False


def action(username, spacename):
    print "Cloning gitlab space %s for user %s " % (spacename, username)
    print "**********************************************"
    client = j.clients.gitlab.get()
    spaces = client.getUserSpacesObjects(username)
    spaces_names = [s['name'] for s in spaces]
    try:
        idx = spaces_names.index(spacename)
        
        web_url = spaces[idx]['web_url'].split('//')
        credentials = "%s:%s" % (client.login, client.passwd)
        web_url.insert(1, '//%s@' % credentials)
        web_url = ''.join(web_url)
        gitlab_spacename = spaces[idx]['namespace']['name']
        basedir = "/opt/jumpscale7/apps/portals/main/base/%s_%s" % (gitlab_spacename, spacename)
        repo = j.clients.git.getClient(basedir=basedir, remoteUrl=web_url)
        repo.fetch()
    except ValueError:
        raise RuntimeError("Insufficient permissions to clone space %s for user %s" % (spacename, username))

if __name__ == '__name__':
    action()