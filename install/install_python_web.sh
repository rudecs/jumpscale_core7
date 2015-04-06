apt-get install mc curl git ssh python2.7 python-requests  -y
set -ex
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/%40ys/install/web/bootstrap_web.py > /var/bootstrap_web.py
cd /var
python /var/bootstrap_web.py
