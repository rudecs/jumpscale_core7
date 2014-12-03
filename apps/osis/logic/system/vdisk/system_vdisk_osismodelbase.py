from JumpScale import j

class system_vdisk_osismodelbase(j.code.classGetJSRootModelBase()):
    def __init__(self):
        pass
        self._P_id=0
        self._P_gid=0
        self._P_nid=0
        self._P_path=""
        self._P_backingpath=""
        self._P_size=0
        self._P_free=0
        self._P_sizeondisk=0
        self._P_fs=""
        self._P_active=True
        self._P_description=""
        self._P_role=""
        self._P_machineid=0
        self._P_order=0
        self._P_type=""
        self._P_backup=True
        self._P_backuptime=0
        self._P_expiration=0
        self._P_backuplocation=""
        self._P_devicename=""
        self._P_lastcheck=0
        self._P_guid=""
        self._P__meta=list()
        self._P__meta=["osismodel","system","vdisk",1] #@todo version not implemented now, just already foreseen

    @property
    def id(self):
        return self._P_id

    @id.setter
    def id(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property id input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_id=value

    @id.deleter
    def id(self):
        del self._P_id

    @property
    def gid(self):
        return self._P_gid

    @gid.setter
    def gid(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property gid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
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
                msg="property nid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
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
                msg="property path input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_path=value

    @path.deleter
    def path(self):
        del self._P_path

    @property
    def backingpath(self):
        return self._P_backingpath

    @backingpath.setter
    def backingpath(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property backingpath input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_backingpath=value

    @backingpath.deleter
    def backingpath(self):
        del self._P_backingpath

    @property
    def size(self):
        return self._P_size

    @size.setter
    def size(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property size input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
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
                msg="property free input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_free=value

    @free.deleter
    def free(self):
        del self._P_free

    @property
    def sizeondisk(self):
        return self._P_sizeondisk

    @sizeondisk.setter
    def sizeondisk(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property sizeondisk input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_sizeondisk=value

    @sizeondisk.deleter
    def sizeondisk(self):
        del self._P_sizeondisk

    @property
    def fs(self):
        return self._P_fs

    @fs.setter
    def fs(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property fs input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_fs=value

    @fs.deleter
    def fs(self):
        del self._P_fs

    @property
    def active(self):
        return self._P_active

    @active.setter
    def active(self, value):
        if not isinstance(value, bool) and value is not None:
            if isinstance(value, basestring) and j.basetype.boolean.checkString(value):
                value = j.basetype.boolean.fromString(value)
            else:
                msg="property active input error, needs to be bool, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_active=value

    @active.deleter
    def active(self):
        del self._P_active

    @property
    def description(self):
        return self._P_description

    @description.setter
    def description(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property description input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_description=value

    @description.deleter
    def description(self):
        del self._P_description

    @property
    def role(self):
        return self._P_role

    @role.setter
    def role(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property role input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_role=value

    @role.deleter
    def role(self):
        del self._P_role

    @property
    def machineid(self):
        return self._P_machineid

    @machineid.setter
    def machineid(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property machineid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_machineid=value

    @machineid.deleter
    def machineid(self):
        del self._P_machineid

    @property
    def order(self):
        return self._P_order

    @order.setter
    def order(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property order input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_order=value

    @order.deleter
    def order(self):
        del self._P_order

    @property
    def type(self):
        return self._P_type

    @type.setter
    def type(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property type input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_type=value

    @type.deleter
    def type(self):
        del self._P_type

    @property
    def backup(self):
        return self._P_backup

    @backup.setter
    def backup(self, value):
        if not isinstance(value, bool) and value is not None:
            if isinstance(value, basestring) and j.basetype.boolean.checkString(value):
                value = j.basetype.boolean.fromString(value)
            else:
                msg="property backup input error, needs to be bool, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_backup=value

    @backup.deleter
    def backup(self):
        del self._P_backup

    @property
    def backuptime(self):
        return self._P_backuptime

    @backuptime.setter
    def backuptime(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property backuptime input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_backuptime=value

    @backuptime.deleter
    def backuptime(self):
        del self._P_backuptime

    @property
    def expiration(self):
        return self._P_expiration

    @expiration.setter
    def expiration(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property expiration input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_expiration=value

    @expiration.deleter
    def expiration(self):
        del self._P_expiration

    @property
    def backuplocation(self):
        return self._P_backuplocation

    @backuplocation.setter
    def backuplocation(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property backuplocation input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_backuplocation=value

    @backuplocation.deleter
    def backuplocation(self):
        del self._P_backuplocation

    @property
    def devicename(self):
        return self._P_devicename

    @devicename.setter
    def devicename(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property devicename input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P_devicename=value

    @devicename.deleter
    def devicename(self):
        del self._P_devicename

    @property
    def lastcheck(self):
        return self._P_lastcheck

    @lastcheck.setter
    def lastcheck(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property lastcheck input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
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
                msg="property guid input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
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
                msg="property _meta input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: vdisk, value was:" + str(value)
                raise TypeError(msg)

        self._P__meta=value

    @_meta.deleter
    def _meta(self):
        del self._P__meta

