from JumpScale import j

class SerializersFactory():

    def __init__(self):
        self.types={}
        self._cache={}

    def get(self,serializationstr,key=""):
        """
        serializationstr FORMATS SUPPORTED FOR NOW
            m=MESSAGEPACK 
            c=COMPRESSION WITH BLOSC
            b=blowfish
            s=snappy
            j=json
            b=base64
            l=lzma
            p=pickle
            r=bin (means is not object (r=raw))
            l=log
            d=dict (check if there is a dict to object, if yes use that dict, removes the private properties (starting with _))

         example serializationstr "mcb" would mean first use messagepack serialization then compress using blosc then encrypt (key will be used)

        this method returns 
        """
        k="%s_%s"%(serializationstr,key)
        if k not in self._cache:
            if len(list(self._cache.keys()))>100:
                self._cache={}
            self._cache[k]= Serializer(serializationstr,key)
        return self._cache[k]

    def getMessagePack(self):
        return self.getSerializerType("m")

    def getBlosc(self):
        return self.getSerializerType("c")

    def getSerializerType(self,type,key=""):
        """
        serializationstr FORMATS SUPPORTED FOR NOW
            m=MESSAGEPACK 
            c=COMPRESSION WITH BLOSC
            b=blowfish
            s=snappy
            j=json
            6=base64
            l=lzma
            p=pickle
            r=bin (means is not object (r=raw))
            l=log
        """
        if type not in self.types:
            if type=="m":
                from .SerializerMSGPack import SerializerMSGPack
                j.db.serializers.msgpack = SerializerMSGPack()
                self.types[type]=j.db.serializers.msgpack
            elif type=="c":
                from .SerializerBlosc import SerializerBlosc
                j.db.serializers.blosc = SerializerBlosc()
                self.types[type]=j.db.serializers.blosc

            elif type=="b":
                from .SerializerBlowfish import SerializerBlowfish
                self.types[type]=SerializerBlowfish(key)

            elif type=="s":
                from .SerializerSnappy import SerializerSnappy
                j.db.serializers.snappy = SerializerSnappy()
                self.types[type]=j.db.serializers.snappy

            elif type=="j":
                from .SerializerUJson import SerializerUJson
                j.db.serializers.ujson = SerializerUJson()
                self.types[type]=j.db.serializers.ujson

            elif type=="d":
                from .SerializerDict import SerializerDict
                j.db.serializers.dict = SerializerDict()
                self.types[type]=j.db.serializers.dict

            elif type=="l":
                from .SerializerLZMA import SerializerLZMA
                j.db.serializers.lzma = SerializerLZMA()
                self.types[type]=j.db.serializers.lzma

            elif type=="p":
                from .SerializerPickle import SerializerPickle
                j.db.serializers.pickle = SerializerPickle()
                self.types[type]=j.db.serializers.pickle

            elif type=="6":
                self.types[type]=j.db.serializers.base64

        return self.types[type]


class Serializer():
    def __init__(self,serializationstr,key=""):
        self.serializationstr=serializationstr
        self.key=key
        for k in self.serializationstr:
            j.db.serializers.getSerializerType(k,self.key)

    def dumps(self,val):
        if self.serializationstr=="":
            return val
        for key in self.serializationstr:
            # print "dumps:%s"%key
            val=j.db.serializers.types[key].dumps(val)
        return val

    def loads(self,data):
        if self.serializationstr=="":
            return data

        for key in reversed(self.serializationstr):
            # print "loads:%s"%key
            data=j.db.serializers.types[key].loads(data)
        return data

