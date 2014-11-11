#!/bin/sh
rsync -av -v install.jumpscale.org::download/test/jsbox/ /opt/jsbox/  --delete-after --modify-window=60 --compress --stats  --progress
rsync -av -v install.jumpscale.org::download/unstable/jsbox_data/ /opt/jsbox_data/  --delete-after --modify-window=60 --compress --stats  --progress
sh /opt/jsbox/tools/init.sh

#export JSBASE=/opt/jsbox

