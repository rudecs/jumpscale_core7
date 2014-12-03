from JumpScale import j

class system_audit_osismodelbase(j.code.classGetJSRootModelBase()):
    def __init__(self):
        pass
        self._P_id=0
        self._P_user=""
        self._P_result=""
        self._P_call=""
        self._P_statuscode=""
        self._P_args=""
        self._P_kwargs=""
        self._P_timestamp=""
        self._P_guid=""
        self._P__meta=list()
        self._P__meta=["osismodel","system","audit",1] #@todo version not implemented now, just already foreseen

    @property
    def id(self):
        return self._P_id

    @id.setter
    def id(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property id input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: audit, value was:" + str(value)
                raise TypeError(msg)

        self._P_id=value

    @id.deleter
    def id(self):
        del self._P_id

    @property
    def user(self):
        return self._P_user

    @user.setter
    def user(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property user input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: audit, value was:" + str(value)
                raise TypeError(msg)

        self._P_user=value

    @user.deleter
    def user(self):
        del self._P_user

    @property
    def result(self):
        return self._P_result

    @result.setter
    def result(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property result input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: audit, value was:" + str(value)
                raise TypeError(msg)

        self._P_result=value

    @result.deleter
    def result(self):
        del self._P_result

    @property
    def call(self):
        return self._P_call

    @call.setter
    def call(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property call input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: audit, value was:" + str(value)
                raise TypeError(msg)

        self._P_call=value

    @call.deleter
    def call(self):
        del self._P_call

    @property
    def statuscode(self):
        return self._P_statuscode

    @statuscode.setter
    def statuscode(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property statuscode input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: audit, value was:" + str(value)
                raise TypeError(msg)

        self._P_statuscode=value

    @statuscode.deleter
    def statuscode(self):
        del self._P_statuscode

    @property
    def args(self):
        return self._P_args

    @args.setter
    def args(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property args input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: audit, value was:" + str(value)
                raise TypeError(msg)

        self._P_args=value

    @args.deleter
    def args(self):
        del self._P_args

    @property
    def kwargs(self):
        return self._P_kwargs

    @kwargs.setter
    def kwargs(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property kwargs input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: audit, value was:" + str(value)
                raise TypeError(msg)

        self._P_kwargs=value

    @kwargs.deleter
    def kwargs(self):
        del self._P_kwargs

    @property
    def timestamp(self):
        return self._P_timestamp

    @timestamp.setter
    def timestamp(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property timestamp input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: audit, value was:" + str(value)
                raise TypeError(msg)

        self._P_timestamp=value

    @timestamp.deleter
    def timestamp(self):
        del self._P_timestamp

    @property
    def guid(self):
        return self._P_guid

    @guid.setter
    def guid(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property guid input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: audit, value was:" + str(value)
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
                msg="property _meta input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: audit, value was:" + str(value)
                raise TypeError(msg)

        self._P__meta=value

    @_meta.deleter
    def _meta(self):
        del self._P__meta

