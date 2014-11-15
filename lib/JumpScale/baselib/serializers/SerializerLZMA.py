
import pylzma

class SerializerLZMA(object):
    def dumps(self,obj):
        return pylzma.compress(obj)
    def loads(self,s):
        return pylzma.decompress(s)