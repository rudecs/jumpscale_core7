import sys
from InstallTools import *

import sys

if len(sys.argv)<3:
    raise RuntimeError("specify login/passwd (as 2 independant args)")

login=sys.argv[1]
passwd=sys.argv[2]


# do.installJS(base="/opt/jumpscale7",clean=True,insystem=False,pythonversion=3,web=True)

from JumpScale import j

import JumpScale.lib.sandboxer

# j.tools.sandboxer.copyLibsTo("/opt/code/git/binary/doublecmd/doublecmd","/tmp/2/",recursive=False)


def get(url):
    cmd="git config --global push.default matching"
    do.execute(cmd)
    do.pullGitRepo(url,dest=None,login=login,passwd=passwd,depth=None,ignorelocalchanges=False,reset=False,branch="master")
    do.pushGitRepos(message="init",name=do.getBaseName(url))

# get("http://git.aydo.com/0-complexity/netwpoc")
# get("http://git.aydo.com/aydo/docs_0disk")

get("http://git.aydo.com/binary/base_python")
# get("http://git.aydo.com/binary/base_python3")
get("http://git.aydo.com/binary/web_python")
# get("http://git.aydo.com/binary/web_python3")

# get("http://git.aydo.com/aydo/mdserver")
# get("http://git.aydo.com/aydo/blobstor")
# get("http://git.aydo.com/aydo/docs")
# get("http://git.aydo.com/aydo/fsgw_fuse")
# get("http://git.aydo.com/aydo/fsgw_win")
# get("http://git.aydo.com/aydo/client")


# get("https://github.com/Jumpscale/aydo")
# get("https://github.com/Jumpscale/web")
get("https://github.com/Jumpscale/jumpscale_core7")
get("https://github.com/Jumpscale/play")
get("https://github.com/Jumpscale/play7")
# get("https://github.com/Jumpscale/jumpscale_core")
# get("https://github.com/Jumpscale/jumpscale_docs")
get("https://github.com/Jumpscale/jumpscale_portal")
get("https://github.com/Jumpscale/jumpscale_examples7")

get("https://github.com/Jumpscale/ays_jumpscale7")

# get("http://git.aydo.com/binary/mongodb")
# get("http://git.aydo.com/binary/lemp")
# get("http://git.aydo.com/binary/node")
# get("http://git.aydo.com/binary/mariadb")
# get("http://git.aydo.com/binary/mariadb_extra")

# get("https://github.com/mrjoes/flask-admin/")

# get("http://git.aydo.com/binary/sublimetext")
# get("http://git.aydo.com/binary/doublecmd")
# get("http://git.aydo.com/binary/go")
# get("http://git.aydo.com/binary/go_extra")
# get("http://git.aydo.com/binary/elasticsearch")
# get("http://git.aydo.com/binary/postgresql")
# get("http://git.aydo.com/binary/redis")
# get("http://git.aydo.com/binary/openresty")
# get("http://git.aydo.com/binary/guacamole")
# get("http://git.aydo.com/binary/java")
# get("http://git.aydo.com/binary/openvpn")
# get("http://git.aydo.com/binary/webmin")
# get("http://git.aydo.com/binary/influxdb")
# get("http://git.aydo.com/binary/lamson")
# get("http://git.aydo.com/binary/collectd")