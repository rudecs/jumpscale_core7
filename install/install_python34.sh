apt-get install mc curl git ssh python3.4 python3-requests  -y
set -ex
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/web/bootstrap34.py > /tmp/bootstrap.py
cd /tmp
python3 bootstrap.py
