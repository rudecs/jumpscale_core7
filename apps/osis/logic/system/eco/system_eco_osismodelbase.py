from JumpScale import j

class system_eco_osismodelbase(j.code.classGetJSRootModelBase()):
    """
    Error Condition Object
    """
    def __init__(self):
        pass
        self._P_id=0
        self._P_gid=0
        self._P_nid=0
        self._P_aid=0
        self._P_pid=0
        self._P_jid=0
        self._P_masterjid=0
        self._P_epoch=0
        self._P_appname=""
        self._P_level=0
        self._P_type=""
        self._P_state=""
        self._P_errormessage=""
        self._P_errormessagePub=""
        self._P_category=""
        self._P_tags=""
        self._P_code=""
        self._P_funcname=""
        self._P_funcfilename=""
        self._P_funclinenr=0
        self._P_backtrace=""
        self._P_backtraceDetailed=""
        self._P_extra=""
        self._P_lasttime=0
        self._P_closetime=0
        self._P_occurrences=0
        self._P_guid=""
        self._P__meta=list()
        self._P__meta=["osismodel","system","eco",1] #@todo version not implemented now, just already foreseen

    @property
    def id(self):
        return self._P_id

    @id.setter
    def id(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property id input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
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
                msg="property gid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
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
                msg="property nid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_nid=value

    @nid.deleter
    def nid(self):
        del self._P_nid

    @property
    def aid(self):
        return self._P_aid

    @aid.setter
    def aid(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property aid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_aid=value

    @aid.deleter
    def aid(self):
        del self._P_aid

    @property
    def pid(self):
        return self._P_pid

    @pid.setter
    def pid(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property pid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_pid=value

    @pid.deleter
    def pid(self):
        del self._P_pid

    @property
    def jid(self):
        return self._P_jid

    @jid.setter
    def jid(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property jid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_jid=value

    @jid.deleter
    def jid(self):
        del self._P_jid

    @property
    def masterjid(self):
        return self._P_masterjid

    @masterjid.setter
    def masterjid(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property masterjid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_masterjid=value

    @masterjid.deleter
    def masterjid(self):
        del self._P_masterjid

    @property
    def epoch(self):
        return self._P_epoch

    @epoch.setter
    def epoch(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property epoch input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_epoch=value

    @epoch.deleter
    def epoch(self):
        del self._P_epoch

    @property
    def appname(self):
        return self._P_appname

    @appname.setter
    def appname(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property appname input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_appname=value

    @appname.deleter
    def appname(self):
        del self._P_appname

    @property
    def level(self):
        return self._P_level

    @level.setter
    def level(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property level input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_level=value

    @level.deleter
    def level(self):
        del self._P_level

    @property
    def type(self):
        return self._P_type

    @type.setter
    def type(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property type input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_type=value

    @type.deleter
    def type(self):
        del self._P_type

    @property
    def state(self):
        return self._P_state

    @state.setter
    def state(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property state input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_state=value

    @state.deleter
    def state(self):
        del self._P_state

    @property
    def errormessage(self):
        return self._P_errormessage

    @errormessage.setter
    def errormessage(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property errormessage input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_errormessage=value

    @errormessage.deleter
    def errormessage(self):
        del self._P_errormessage

    @property
    def errormessagePub(self):
        return self._P_errormessagePub

    @errormessagePub.setter
    def errormessagePub(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property errormessagePub input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_errormessagePub=value

    @errormessagePub.deleter
    def errormessagePub(self):
        del self._P_errormessagePub

    @property
    def category(self):
        return self._P_category

    @category.setter
    def category(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property category input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_category=value

    @category.deleter
    def category(self):
        del self._P_category

    @property
    def tags(self):
        return self._P_tags

    @tags.setter
    def tags(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property tags input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_tags=value

    @tags.deleter
    def tags(self):
        del self._P_tags

    @property
    def code(self):
        return self._P_code

    @code.setter
    def code(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property code input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_code=value

    @code.deleter
    def code(self):
        del self._P_code

    @property
    def funcname(self):
        return self._P_funcname

    @funcname.setter
    def funcname(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property funcname input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_funcname=value

    @funcname.deleter
    def funcname(self):
        del self._P_funcname

    @property
    def funcfilename(self):
        return self._P_funcfilename

    @funcfilename.setter
    def funcfilename(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property funcfilename input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_funcfilename=value

    @funcfilename.deleter
    def funcfilename(self):
        del self._P_funcfilename

    @property
    def funclinenr(self):
        return self._P_funclinenr

    @funclinenr.setter
    def funclinenr(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property funclinenr input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_funclinenr=value

    @funclinenr.deleter
    def funclinenr(self):
        del self._P_funclinenr

    @property
    def backtrace(self):
        return self._P_backtrace

    @backtrace.setter
    def backtrace(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property backtrace input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_backtrace=value

    @backtrace.deleter
    def backtrace(self):
        del self._P_backtrace

    @property
    def backtraceDetailed(self):
        return self._P_backtraceDetailed

    @backtraceDetailed.setter
    def backtraceDetailed(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property backtraceDetailed input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_backtraceDetailed=value

    @backtraceDetailed.deleter
    def backtraceDetailed(self):
        del self._P_backtraceDetailed

    @property
    def extra(self):
        return self._P_extra

    @extra.setter
    def extra(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property extra input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_extra=value

    @extra.deleter
    def extra(self):
        del self._P_extra

    @property
    def lasttime(self):
        return self._P_lasttime

    @lasttime.setter
    def lasttime(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property lasttime input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_lasttime=value

    @lasttime.deleter
    def lasttime(self):
        del self._P_lasttime

    @property
    def closetime(self):
        return self._P_closetime

    @closetime.setter
    def closetime(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property closetime input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_closetime=value

    @closetime.deleter
    def closetime(self):
        del self._P_closetime

    @property
    def occurrences(self):
        return self._P_occurrences

    @occurrences.setter
    def occurrences(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property occurrences input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P_occurrences=value

    @occurrences.deleter
    def occurrences(self):
        del self._P_occurrences

    @property
    def guid(self):
        return self._P_guid

    @guid.setter
    def guid(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property guid input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
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
                msg="property _meta input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: eco, value was:" + str(value)
                raise TypeError(msg)

        self._P__meta=value

    @_meta.deleter
    def _meta(self):
        del self._P__meta

