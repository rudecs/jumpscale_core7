
import struct

class SerializerCRC(object):
    def dumps(self,obj):
        j.tools.hash.crc32_string(obj)
        return obj
    def loads(self,s):
        return s[4:]