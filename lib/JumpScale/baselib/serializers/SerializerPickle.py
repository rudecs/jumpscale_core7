
import cPickle


class SerializerPickle(object):
    def dumps(self,obj):
        return  cPickle.dumps(obj)
    def loads(self,s):
        return cPickle.loads(s)