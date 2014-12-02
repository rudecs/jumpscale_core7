from JumpScale import j

class system_disk_osismodelbase(j.code.classGetJSRootModelBase()):
    def __init__(self):
        pass
        self._P_id=0
        self._P_partnr=0
        self._P_gid=0
        self._P_nid=0
        self._P_path=""
        self._P_size=0
        self._P_free=0
        self._P_ssd=0
        self._P_fs=""
        self._P_mounted=True
        self._P_mountpoint=""
        self._P_active=True
        self._P_model=""
        self._P_description=""
        self._P_type=list()
        self._P_lastcheck=""
        self._P_guid=""
        self._P__meta=list()
        self._P__meta=["osismodel","system","disk",1] #@todo version not implemented now, just already foreseen

    @property
    def id(self):
        return self._P_id

    @id.setter
    def id(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property id input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_id=value

    @id.deleter
    def id(self):
        del self._P_id

    @property
    def partnr(self):
        return self._P_partnr

    @partnr.setter
    def partnr(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property partnr input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_partnr=value

    @partnr.deleter
    def partnr(self):
        del self._P_partnr

    @property
    def gid(self):
        return self._P_gid

    @gid.setter
    def gid(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property gid input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_gid=value

    @gid.deleter
    def gid(self):
        del self._P_gid

    @property
    def nid(self):
        return self._P_nid

    @nid.setter
    def nid(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property nid input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_nid=value

    @nid.deleter
    def nid(self):
        del self._P_nid

    @property
    def path(self):
        return self._P_path

    @path.setter
    def path(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property path input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_path=value

    @path.deleter
    def path(self):
        del self._P_path

    @property
    def size(self):
        return self._P_size

    @size.setter
    def size(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property size input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_size=value

    @size.deleter
    def size(self):
        del self._P_size

    @property
    def free(self):
        return self._P_free

    @free.setter
    def free(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property free input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_free=value

    @free.deleter
    def free(self):
        del self._P_free

    @property
    def ssd(self):
        return self._P_ssd

    @ssd.setter
    def ssd(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property ssd input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_ssd=value

    @ssd.deleter
    def ssd(self):
        del self._P_ssd

    @property
    def fs(self):
        return self._P_fs

    @fs.setter
    def fs(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property fs input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_fs=value

    @fs.deleter
    def fs(self):
        del self._P_fs

    @property
    def mounted(self):
        return self._P_mounted

    @mounted.setter
    def mounted(self, value):
        if not isinstance(value, bool) and value is not None:
            if isinstance(value, basestring) and j.basetype.boolean.checkString(value):
                value = j.basetype.boolean.fromString(value)
            else:
                msg="property mounted input error, needs to be bool, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_mounted=value

    @mounted.deleter
    def mounted(self):
        del self._P_mounted

    @property
    def mountpoint(self):
        return self._P_mountpoint

    @mountpoint.setter
    def mountpoint(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property mountpoint input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_mountpoint=value

    @mountpoint.deleter
    def mountpoint(self):
        del self._P_mountpoint

    @property
    def active(self):
        return self._P_active

    @active.setter
    def active(self, value):
        if not isinstance(value, bool) and value is not None:
            if isinstance(value, basestring) and j.basetype.boolean.checkString(value):
                value = j.basetype.boolean.fromString(value)
            else:
                msg="property active input error, needs to be bool, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_active=value

    @active.deleter
    def active(self):
        del self._P_active

    @property
    def model(self):
        return self._P_model

    @model.setter
    def model(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property model input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_model=value

    @model.deleter
    def model(self):
        del self._P_model

    @property
    def description(self):
        return self._P_description

    @description.setter
    def description(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property description input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_description=value

    @description.deleter
    def description(self):
        del self._P_description

    @property
    def type(self):
        return self._P_type

    @type.setter
    def type(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property type input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_type=value

    @type.deleter
    def type(self):
        del self._P_type

    @property
    def lastcheck(self):
        return self._P_lastcheck

    @lastcheck.setter
    def lastcheck(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property lastcheck input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P_lastcheck=value

    @lastcheck.deleter
    def lastcheck(self):
        del self._P_lastcheck

    @property
    def guid(self):
        return self._P_guid

    @guid.setter
    def guid(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property guid input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
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
                msg="property _meta input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: disk, value was:" + str(value)
                raise TypeError(msg)

        self._P__meta=value

    @_meta.deleter
    def _meta(self):
        del self._P__meta

