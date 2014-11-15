
import struct

class SerializerBase64(object):
    def dumps(self,obj):
        return obj.encode("base64")
        
    def loads(self,s):
        return s.decode("base64")