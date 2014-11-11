#!/bin/sh

RSYNCSERVER=install.jumpscale.org
if [ -n "$1" ]; then
    RSYNCSERVER=$1
fi

mkdir -p /opt/jsbox
rsync -av -v $RSYNCSERVER::download/stable/jsbox/ /opt/jsbox/  --delete-after --modify-window=60 --compress --stats  --progress
rsync -av -v $RSYNCSERVER::download/stable/jsbox_data/ /opt/jsbox_data/  --delete-after --modify-window=60 --compress --stats  --progress
rm -rf /opt/jsbox/cfg #resolve a bug

#source /opt/jsbox/activate

echo "JSBOX has been installed to activate it run 'source /opt/jsbox/activate'"
