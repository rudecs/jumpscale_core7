apt-get install mc curl git ssh python3.4 python3-requests  -y
set +ex
rm -f /tmp/bootstrap.py
rm -f /tmp/InstallTools.py
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/%40ys/install/web/bootstrap34.py > /tmp/bootstrap.py
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/%40ys/install/InstallTools.py > /tmp/InstallTools.py
cd /tmp
python3 bootstrap.py
