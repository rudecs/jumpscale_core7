from JumpScale import j

class system_info_osismodelbase(j.code.classGetJSRootModelBase()):
    def __init__(self):
        pass
        self._P_nid=0
        self._P_gid=0
        self._P_category=""
        self._P_content=""
        self._P_epoch=0
        self._P_id=0
        self._P_guid=""
        self._P__meta=list()
        self._P__meta=["osismodel","system","info",1] #@todo version not implemented now, just already foreseen

    @property
    def nid(self):
        return self._P_nid

    @nid.setter
    def nid(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property nid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: info, value was:" + str(value)
                raise TypeError(msg)

        self._P_nid=value

    @nid.deleter
    def nid(self):
        del self._P_nid

    @property
    def gid(self):
        return self._P_gid

    @gid.setter
    def gid(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property gid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: info, value was:" + str(value)
                raise TypeError(msg)

        self._P_gid=value

    @gid.deleter
    def gid(self):
        del self._P_gid

    @property
    def category(self):
        return self._P_category

    @category.setter
    def category(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property category input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: info, value was:" + str(value)
                raise TypeError(msg)

        self._P_category=value

    @category.deleter
    def category(self):
        del self._P_category

    @property
    def content(self):
        return self._P_content

    @content.setter
    def content(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property content input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: info, value was:" + str(value)
                raise TypeError(msg)

        self._P_content=value

    @content.deleter
    def content(self):
        del self._P_content

    @property
    def epoch(self):
        return self._P_epoch

    @epoch.setter
    def epoch(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property epoch input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: info, value was:" + str(value)
                raise TypeError(msg)

        self._P_epoch=value

    @epoch.deleter
    def epoch(self):
        del self._P_epoch

    @property
    def id(self):
        return self._P_id

    @id.setter
    def id(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property id input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: info, value was:" + str(value)
                raise TypeError(msg)

        self._P_id=value

    @id.deleter
    def id(self):
        del self._P_id

    @property
    def guid(self):
        return self._P_guid

    @guid.setter
    def guid(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property guid input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: info, value was:" + str(value)
                raise TypeError(msg)

        self._P_guid=value

    @guid.deleter
    def guid(self):
        del self._P_guid

    @property
    def _meta(self):
        return self._P__meta

    @_meta.setter
    def _meta(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property _meta input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: info, value was:" + str(value)
                raise TypeError(msg)

        self._P__meta=value

    @_meta.deleter
    def _meta(self):
        del self._P__meta

