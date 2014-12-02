from JumpScale import j

class system_user_osismodelbase(j.code.classGetJSRootModelBase()):
    def __init__(self):
        pass
        self._P_id=0
        self._P_domain=""
        self._P_gid=0
        self._P_passwd=""
        self._P_roles=list()
        self._P_active=True
        self._P_description=""
        self._P_emails=list()
        self._P_xmpp=list()
        self._P_mobile=list()
        self._P_lastcheck=0
        self._P_groups=list()
        self._P_authkey=""
        self._P_data=""
        self._P_authkeys=list()
        self._P_guid=""
        self._P__meta=list()
        self._P__meta=["osismodel","system","user",1] #@todo version not implemented now, just already foreseen

    @property
    def id(self):
        return self._P_id

    @id.setter
    def id(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property id input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_id=value

    @id.deleter
    def id(self):
        del self._P_id

    @property
    def domain(self):
        return self._P_domain

    @domain.setter
    def domain(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property domain input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_domain=value

    @domain.deleter
    def domain(self):
        del self._P_domain

    @property
    def gid(self):
        return self._P_gid

    @gid.setter
    def gid(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property gid input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_gid=value

    @gid.deleter
    def gid(self):
        del self._P_gid

    @property
    def passwd(self):
        return self._P_passwd

    @passwd.setter
    def passwd(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property passwd input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_passwd=value

    @passwd.deleter
    def passwd(self):
        del self._P_passwd

    @property
    def roles(self):
        return self._P_roles

    @roles.setter
    def roles(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property roles input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_roles=value

    @roles.deleter
    def roles(self):
        del self._P_roles

    @property
    def active(self):
        return self._P_active

    @active.setter
    def active(self, value):
        if not isinstance(value, bool) and value is not None:
            if isinstance(value, basestring) and j.basetype.boolean.checkString(value):
                value = j.basetype.boolean.fromString(value)
            else:
                msg="property active input error, needs to be bool, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
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
                msg="property description input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_description=value

    @description.deleter
    def description(self):
        del self._P_description

    @property
    def emails(self):
        return self._P_emails

    @emails.setter
    def emails(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property emails input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_emails=value

    @emails.deleter
    def emails(self):
        del self._P_emails

    @property
    def xmpp(self):
        return self._P_xmpp

    @xmpp.setter
    def xmpp(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property xmpp input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_xmpp=value

    @xmpp.deleter
    def xmpp(self):
        del self._P_xmpp

    @property
    def mobile(self):
        return self._P_mobile

    @mobile.setter
    def mobile(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property mobile input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_mobile=value

    @mobile.deleter
    def mobile(self):
        del self._P_mobile

    @property
    def lastcheck(self):
        return self._P_lastcheck

    @lastcheck.setter
    def lastcheck(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property lastcheck input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_lastcheck=value

    @lastcheck.deleter
    def lastcheck(self):
        del self._P_lastcheck

    @property
    def groups(self):
        return self._P_groups

    @groups.setter
    def groups(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property groups input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_groups=value

    @groups.deleter
    def groups(self):
        del self._P_groups

    @property
    def authkey(self):
        return self._P_authkey

    @authkey.setter
    def authkey(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property authkey input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_authkey=value

    @authkey.deleter
    def authkey(self):
        del self._P_authkey

    @property
    def data(self):
        return self._P_data

    @data.setter
    def data(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property data input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_data=value

    @data.deleter
    def data(self):
        del self._P_data

    @property
    def authkeys(self):
        return self._P_authkeys

    @authkeys.setter
    def authkeys(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property authkeys input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P_authkeys=value

    @authkeys.deleter
    def authkeys(self):
        del self._P_authkeys

    @property
    def guid(self):
        return self._P_guid

    @guid.setter
    def guid(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property guid input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
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
                msg="property _meta input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: user, value was:" + str(value)
                raise TypeError(msg)

        self._P__meta=value

    @_meta.deleter
    def _meta(self):
        del self._P__meta

