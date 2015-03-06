
from JumpScale import j
from JumpScale.baselib import gitlab
from JumpScale.baselib import git
import sys
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
    hrd = j.application.getAppInstanceHRD(name='portal', instance='main')
    gitlabcontentdir = hrd.getStr('param.cfg.contentdirs')
    print "Cloning gitlab spaces for user %s " % username
    print "**********************************************"
    client = j.clients.gitlab.get()
    projects = client.getUserSpacesObjects(username)
    for p in projects:
        web_url = p['web_url'].split('//')
        credentials = "%s:%s" % (client.login, client.passwd)
        web_url.insert(1, '//%s@' % credentials)
        web_url = ''.join(web_url)
        basedir = "%s/%s_%s" % (gitlabcontentdir, p['namespace']['name'], p['name'])
        repo = j.clients.git.getClient(basedir=basedir, remoteUrl=web_url)
        repo.fetch()

if __name__ == '__main__':
    if not len(sys.argv) == 2:
        print "Please pass gitlab username"
    else:
        action(sys.argv[1])