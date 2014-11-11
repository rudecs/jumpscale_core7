__version__ = '6.0.0'
__all__ = ['__version__', 'j']


import pkgutil
__path__ = pkgutil.extend_path(__path__, __name__)
del pkgutil

import sys
import os

if 'JSBASE' in os.environ:
    home = os.environ['JSBASE']
    sys.path=['', '%s/bin'%home,'%s/bin/core.zip'%home,'%s/lib'%home,'%s/libjs'%home,\
        '%s/lib/python.zip'%home,'%s/libext'%home,'%s/lib/JumpScale.zip'%home]

class JumpScale():
	def __init__(self):
		pass

j = JumpScale()
from . import base
from . import core
