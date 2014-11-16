
do bootstrap do

#if ubuntu is in recent state & apt get update was done recently
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/bootstrap/bootstrap.sh | bash

or
#to also update/upgrade ubuntu first
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/bootstrap/bootstrap_updateubuntu.sh | bash