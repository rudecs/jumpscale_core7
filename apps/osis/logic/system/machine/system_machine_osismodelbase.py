from JumpScale import j

class system_machine_osismodelbase(j.code.classGetJSRootModelBase()):
    def __init__(self):
        pass
        self._P_id=0
        self._P_gid=0
        self._P_nid=0
        self._P_name=""
        self._P_roles=list()
        self._P_netaddr=""
        self._P_ipaddr=list()
        self._P_active=True
        self._P_state=""
        self._P_mem=0
        self._P_cpucore=0
        self._P_description=""
        self._P_otherid=""
        self._P_type=""
        self._P_lastcheck=0
        self._P_guid=""
        self._P__meta=list()
        self._P__meta=["osismodel","system","machine",1] #@todo version not implemented now, just already foreseen

    @property
    def id(self):
        return self._P_id

    @id.setter
    def id(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property id input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
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
                msg="property gid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
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
                msg="property nid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
                raise TypeError(msg)

        self._P_nid=value

    @nid.deleter
    def nid(self):
        del self._P_nid

    @property
    def name(self):
        return self._P_name

    @name.setter
    def name(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property name input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
                raise TypeError(msg)

        self._P_name=value

    @name.deleter
    def name(self):
        del self._P_name

    @property
    def roles(self):
        return self._P_roles

    @roles.setter
    def roles(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property roles input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
                raise TypeError(msg)

        self._P_roles=value

    @roles.deleter
    def roles(self):
        del self._P_roles

    @property
    def netaddr(self):
        return self._P_netaddr

    @netaddr.setter
    def netaddr(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property netaddr input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
                raise TypeError(msg)

        self._P_netaddr=value

    @netaddr.deleter
    def netaddr(self):
        del self._P_netaddr

    @property
    def ipaddr(self):
        return self._P_ipaddr

    @ipaddr.setter
    def ipaddr(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property ipaddr input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
                raise TypeError(msg)

        self._P_ipaddr=value

    @ipaddr.deleter
    def ipaddr(self):
        del self._P_ipaddr

    @property
    def active(self):
        return self._P_active

    @active.setter
    def active(self, value):
        if not isinstance(value, bool) and value is not None:
            if isinstance(value, basestring) and j.basetype.boolean.checkString(value):
                value = j.basetype.boolean.fromString(value)
            else:
                msg="property active input error, needs to be bool, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
                raise TypeError(msg)

        self._P_active=value

    @active.deleter
    def active(self):
        del self._P_active

    @property
    def state(self):
        return self._P_state

    @state.setter
    def state(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property state input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
                raise TypeError(msg)

        self._P_state=value

    @state.deleter
    def state(self):
        del self._P_state

    @property
    def mem(self):
        return self._P_mem

    @mem.setter
    def mem(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property mem input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
                raise TypeError(msg)

        self._P_mem=value

    @mem.deleter
    def mem(self):
        del self._P_mem

    @property
    def cpucore(self):
        return self._P_cpucore

    @cpucore.setter
    def cpucore(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property cpucore input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
                raise TypeError(msg)

        self._P_cpucore=value

    @cpucore.deleter
    def cpucore(self):
        del self._P_cpucore

    @property
    def description(self):
        return self._P_description

    @description.setter
    def description(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property description input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
                raise TypeError(msg)

        self._P_description=value

    @description.deleter
    def description(self):
        del self._P_description

    @property
    def otherid(self):
        return self._P_otherid

    @otherid.setter
    def otherid(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property otherid input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
                raise TypeError(msg)

        self._P_otherid=value

    @otherid.deleter
    def otherid(self):
        del self._P_otherid

    @property
    def type(self):
        return self._P_type

    @type.setter
    def type(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property type input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
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
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property lastcheck input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
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
                msg="property guid input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
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
                msg="property _meta input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: machine, value was:" + str(value)
                raise TypeError(msg)

        self._P__meta=value

    @_meta.deleter
    def _meta(self):
        del self._P__meta

