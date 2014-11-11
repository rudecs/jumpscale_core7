from JumpScale import j
from JumpScale.grid.osis.OSISStore import OSISStore
ujson = j.db.serializers.getSerializerType('j')


class mainclass(OSISStore):

    """
    Default object implementation
    """

    # def set(self, key, value):
    #     """
    #     value can be a dict or a raw value (seen as string)
    #     if raw value then will not try to index
    #     """
    #     if j.basetype.dictionary.check(value):
    #         #is probably an osis object
    #         if value.has_key("_meta") and  value.has_key("_ckey"):
    #             #is an osis object
    #             new,changed,obj=self._setObjIds(value)
    #             self.index(obj)
    #             return (new,changed,obj)
        
    #     #not an osis obj, need to stor as raw value
    #     self.db.set(self.dbprefix, key=key, value=value)


