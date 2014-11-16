set -ex
apt-get update
apt-get autoremove
apt-get -f install -y
apt-get upgrade -y
apt-get install mc curl git ssh python2.7 python-requests  -y
curl http://git.aydo.com/aydo/docs_0disk/raw/master/getstarted/bootstrap.py | python 