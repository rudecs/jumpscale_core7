try:
    import ujson as json
except ImportError:
    import json
 

class SerializerUJson(object):
    def dumps(self,obj):
        return json.dumps(obj, ensure_ascii=False)
    def loads(self,s):
        return json.loads(s)
