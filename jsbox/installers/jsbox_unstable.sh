#!/bin/sh
export RSYNCSERVER=install.jumpscale.org
set -ex
rsync -av -v $RSYNCSERVER::download/unstable/jsbox/ /opt/jsbox2/  --delete-after --modify-window=60 --compress --stats  --progress
rsync -av -v $RSYNCSERVER::download/unstable/jsbox_data/ /opt/jsbox2_data/  --delete-after --modify-window=60 --compress --stats  --progress

#source /opt/jsbox2/activate

echo "JSBOX has been installed to activate it run 'source /opt/jsbox2/activate'"


