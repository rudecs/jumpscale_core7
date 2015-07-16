if [ -f "/etc/slitaz-release" ]
then
  echo "found slitaz"
  tazpkg get-install curl 
  tazpkg get-install git
  tazpkg get-install python 
fi

dist=`grep DISTRIB_ID /etc/*-release | awk -F '=' '{print $2}'`
if [ "$dist" == "Ubuntu" ]; then
  echo "found ubuntu"
  apt-get install curl git ssh python2.7 -y
fi

set -ex
curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/web/bootstrap.py > /tmp/bootstrap.py
cd /tmp
python /tmp/bootstrap.py
