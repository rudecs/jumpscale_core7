#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import re
import os
import glob
import sys

scripts = glob.glob('shellcmds/*')

def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.match("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)

version = get_version('lib/JumpScale')


def clean():
    print "CLEAN"
    for r,d,f in os.walk("/usr"):
      for path in f:
          match=False
          if path.startswith("jscode") or path.startswith("jpackage") or path.startswith("jspackage") or path.startswith("jsdevelop")\
              or path.startswith("jsreinstall") or path.startswith("jsprocess") or path.startswith("jslog") or path.startswith("jsshell") or path.startswith("osis"):
              match=True
          if path in ["js"]:
              match=True      
          if match:
              print "remove:%s" % os.path.join(r,path)
              os.remove(os.path.join(r,path))
    cmds="""
killall tmux
rm -rf /usr/local/lib/python2.7/dist-packages/jumpscale*
rm -rf /usr/local/lib/python2.7/site-packages/jumpscale*
rm -rf /usr/local/lib/python2.7/dist-packages/JumpScale*
rm -rf /usr/local/lib/python2.7/site-packages/JumpScale*
rm -rf /usr/local/lib/python2.7/site-packages/JumpScale/
rm -rf /usr/local/lib/python2.7/site-packages/jumpscale/
rm -rf /usr/local/lib/python2.7/dist-packages/JumpScale/
rm -rf /usr/local/lib/python2.7/dist-packages/jumpscale/
rm /usr/local/bin/js*
rm /usr/local/bin/jpack*
"""    
    for cmd in cmds.split("\n"):
      if cmd.strip()<>"":
          rc=os.system("%s 2>&1 > /dev/null; echo"%cmd)
clean()

def list_files(basedir='.', subdir='.'):
    package_data = []
    basedir_length = len(basedir)
    for dirpath, dirs, files in os.walk(os.path.join(basedir,subdir)):
        for file in files:
            package_data.append(os.path.join(dirpath[basedir_length+1:],file))
    return package_data
            

setup(name='JumpScale-core',
      version=version,
      description='Python Automation framework',
      author='JumpScale',
      author_email='info@jumpscale.org',
      url='http://www.jumpscale.org',
      license='BSD 2-Clause',
      packages = find_packages('lib'),
      package_dir = {'':'lib'},
      include_package_data = True,
      package_data = {'JumpScale':list_files(basedir='lib/JumpScale',subdir='core/_defaultcontent') +
                                  list_files(basedir='lib/JumpScale',subdir='baselib/jpackages/templates')
                     },
      scripts=scripts,

      download_url='http://pypi.python.org/pypi/JumpScale/',
      install_requires=[],
      classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
    ]
)
