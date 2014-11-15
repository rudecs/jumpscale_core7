
import blosc

class SerializerBlosc(object):
    def dumps(self,obj):        
        return  blosc.compress(obj, typesize=8)
    def loads(self,s):
        return blosc.decompress(s)