from JumpScale import j

class system_alert_osismodelbase(j.code.classGetJSRootModelBase()):
    def __init__(self):
        pass
        self._P_id=0
        self._P_gid=0
        self._P_nid=0
        self._P_description=""
        self._P_descriptionpub=""
        self._P_level=0
        self._P_category=""
        self._P_tags=""
        self._P_state=""
        self._P_inittime=0
        self._P_lasttime=0
        self._P_closetime=0
        self._P_nrerrorconditions=0
        self._P_errorconditions=list()
        self._P_guid=""
        self._P__meta=list()
        self._P__meta=["osismodel","system","alert",1] #@todo version not implemented now, just already foreseen

    @property
    def id(self):
        return self._P_id

    @id.setter
    def id(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property id input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
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
                msg="property gid input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
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
                msg="property nid input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
                raise TypeError(msg)

        self._P_nid=value

    @nid.deleter
    def nid(self):
        del self._P_nid

    @property
    def description(self):
        return self._P_description

    @description.setter
    def description(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property description input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
                raise TypeError(msg)

        self._P_description=value

    @description.deleter
    def description(self):
        del self._P_description

    @property
    def descriptionpub(self):
        return self._P_descriptionpub

    @descriptionpub.setter
    def descriptionpub(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property descriptionpub input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
                raise TypeError(msg)

        self._P_descriptionpub=value

    @descriptionpub.deleter
    def descriptionpub(self):
        del self._P_descriptionpub

    @property
    def level(self):
        return self._P_level

    @level.setter
    def level(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property level input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
                raise TypeError(msg)

        self._P_level=value

    @level.deleter
    def level(self):
        del self._P_level

    @property
    def category(self):
        return self._P_category

    @category.setter
    def category(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property category input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
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
                msg="property tags input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
                raise TypeError(msg)

        self._P_tags=value

    @tags.deleter
    def tags(self):
        del self._P_tags

    @property
    def state(self):
        return self._P_state

    @state.setter
    def state(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property state input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
                raise TypeError(msg)

        self._P_state=value

    @state.deleter
    def state(self):
        del self._P_state

    @property
    def inittime(self):
        return self._P_inittime

    @inittime.setter
    def inittime(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property inittime input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
                raise TypeError(msg)

        self._P_inittime=value

    @inittime.deleter
    def inittime(self):
        del self._P_inittime

    @property
    def lasttime(self):
        return self._P_lasttime

    @lasttime.setter
    def lasttime(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property lasttime input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
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
                msg="property closetime input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
                raise TypeError(msg)

        self._P_closetime=value

    @closetime.deleter
    def closetime(self):
        del self._P_closetime

    @property
    def nrerrorconditions(self):
        return self._P_nrerrorconditions

    @nrerrorconditions.setter
    def nrerrorconditions(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property nrerrorconditions input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
                raise TypeError(msg)

        self._P_nrerrorconditions=value

    @nrerrorconditions.deleter
    def nrerrorconditions(self):
        del self._P_nrerrorconditions

    @property
    def errorconditions(self):
        return self._P_errorconditions

    @errorconditions.setter
    def errorconditions(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property errorconditions input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
                raise TypeError(msg)

        self._P_errorconditions=value

    @errorconditions.deleter
    def errorconditions(self):
        del self._P_errorconditions

    @property
    def guid(self):
        return self._P_guid

    @guid.setter
    def guid(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property guid input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
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
                msg="property _meta input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: alert, value was:" + str(value)
                raise TypeError(msg)

        self._P__meta=value

    @_meta.deleter
    def _meta(self):
        del self._P__meta

