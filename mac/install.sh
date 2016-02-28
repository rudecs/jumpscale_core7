#install btsync & get following link
#https://link.getsync.com/#f=mac_apps&sz=22E7&t=2&s=426SLEDUASCIWV6ALQYMJRND2L5KNTU6ES5WK4PTL4EI74KO3XUQ&i=C52JRGNYKYRD25O2UKSQSA76WHL6I3WJB&v=2.0
#install in /Users/Shared/sync/mac_apps

#i did wrong so created symlink
#ln -s '/Users/kristofdespiegeleer1/BitTorrent Sync/mac_apps/' /Users/Shared/sync/mac_apps

#install python 2.7
#install wxpython cocoa

mkdir -p /Users/Shared/sync/code/
cd /Users/Shared/sync/code/
git clone https://despiegk:????@github.com/jumpscale7/jumpscale_core7.git
git checkout -b @ys --track origin/@ys

#install brew	
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

brew install git
brew install vim
brew install curl
brew install wget
brew install homebrew/x11/meld


pip install ipython
pip install ujson
pip install scandir
pip install snappy
pip install pylzma
pip install psutil
pip install blosc
pip install cffi
pip install gevent
# pip install lzo
pip install pillow
pip install flask
pip install psutil
pip install flask-swagger
pip install flask-classy

echo '/Users/Shared/code/jumpscale_core7/lib/' > /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/JumpScale.pth
echo '/Users/Shared/code/jumpscale_core7/install/' >> /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/JumpScale.pth

#copy code completion for sublime
cp '/Users/Shared/sync/mac_apps/install/Sublime Text Packages/JumpScale.sublime-package' '/Volumes/Macintosh HD/Applications/Sublime Text 2.app/Contents/MacOS/Pristine Packages/'

#copy basic jumpscale files
rsync -rav /Users/Shared/sync/mac_apps/install/jumpscale/ /Users/Shared/jumpscale/


