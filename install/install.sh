apt-get install mc curl git ssh python2.7 python-requests  -y
set -ex
curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/web/bootstrap.py > /tmp/bootstrap.py
cd /tmp
python /tmp/bootstrap.py
