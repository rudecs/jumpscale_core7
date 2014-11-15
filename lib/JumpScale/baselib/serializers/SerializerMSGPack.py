
import msgpack

class SerializerMSGPack(object):
    def dumps(self,obj):
        return msgpack.packb(obj)
    def loads(self,s):
        return msgpack.unpackb(s)