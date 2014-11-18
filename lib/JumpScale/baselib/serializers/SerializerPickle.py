
import pickle


class SerializerPickle(object):
    def dumps(self,obj):
        return  pickle.dumps(obj)
    def loads(self,s):
        return pickle.loads(s)