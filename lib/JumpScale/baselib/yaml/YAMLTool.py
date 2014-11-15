
from JumpScale import j

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
    

class YAMLTool:
    def decode(self,string):
        """
        decode yaml string to python object
        """
        return load(string)
        
    def encode(self,obj,width=120):
        """
        encode python (simple) objects to yaml
        """
        return dump(obj, width=width, default_flow_style=False)
        
