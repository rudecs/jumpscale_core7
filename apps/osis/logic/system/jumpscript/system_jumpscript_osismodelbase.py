from JumpScale import j

class system_jumpscript_osismodelbase(j.code.classGetJSRootModelBase()):
    def __init__(self):
        pass
        self._P_id=0
        self._P_gid=0
        self._P_name=""
        self._P_descr=""
        self._P_category=""
        self._P_organization=""
        self._P_author=""
        self._P_license=""
        self._P_version=""
        self._P_roles=list()
        self._P_action=""
        self._P_source=""
        self._P_path=""
        self._P_args=list()
        self._P_enabled=True
        self._P_async=True
        self._P_period=0
        self._P_order=0
        self._P_queue=""
        self._P_log=True
        self._P_guid=""
        self._P__meta=list()
        self._P__meta=["osismodel","system","jumpscript",1] #@todo version not implemented now, just already foreseen

    @property
    def id(self):
        return self._P_id

    @id.setter
    def id(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property id input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
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
                msg="property gid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_gid=value

    @gid.deleter
    def gid(self):
        del self._P_gid

    @property
    def name(self):
        return self._P_name

    @name.setter
    def name(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property name input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_name=value

    @name.deleter
    def name(self):
        del self._P_name

    @property
    def descr(self):
        return self._P_descr

    @descr.setter
    def descr(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property descr input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_descr=value

    @descr.deleter
    def descr(self):
        del self._P_descr

    @property
    def category(self):
        return self._P_category

    @category.setter
    def category(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property category input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_category=value

    @category.deleter
    def category(self):
        del self._P_category

    @property
    def organization(self):
        return self._P_organization

    @organization.setter
    def organization(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property organization input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_organization=value

    @organization.deleter
    def organization(self):
        del self._P_organization

    @property
    def author(self):
        return self._P_author

    @author.setter
    def author(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property author input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_author=value

    @author.deleter
    def author(self):
        del self._P_author

    @property
    def license(self):
        return self._P_license

    @license.setter
    def license(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property license input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_license=value

    @license.deleter
    def license(self):
        del self._P_license

    @property
    def version(self):
        return self._P_version

    @version.setter
    def version(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property version input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_version=value

    @version.deleter
    def version(self):
        del self._P_version

    @property
    def roles(self):
        return self._P_roles

    @roles.setter
    def roles(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property roles input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_roles=value

    @roles.deleter
    def roles(self):
        del self._P_roles

    @property
    def action(self):
        return self._P_action

    @action.setter
    def action(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property action input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_action=value

    @action.deleter
    def action(self):
        del self._P_action

    @property
    def source(self):
        return self._P_source

    @source.setter
    def source(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property source input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_source=value

    @source.deleter
    def source(self):
        del self._P_source

    @property
    def path(self):
        return self._P_path

    @path.setter
    def path(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property path input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_path=value

    @path.deleter
    def path(self):
        del self._P_path

    @property
    def args(self):
        return self._P_args

    @args.setter
    def args(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property args input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_args=value

    @args.deleter
    def args(self):
        del self._P_args

    @property
    def enabled(self):
        return self._P_enabled

    @enabled.setter
    def enabled(self, value):
        if not isinstance(value, bool) and value is not None:
            if isinstance(value, basestring) and j.basetype.boolean.checkString(value):
                value = j.basetype.boolean.fromString(value)
            else:
                msg="property enabled input error, needs to be bool, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_enabled=value

    @enabled.deleter
    def enabled(self):
        del self._P_enabled

    @property
    def async(self):
        return self._P_async

    @async.setter
    def async(self, value):
        if not isinstance(value, bool) and value is not None:
            if isinstance(value, basestring) and j.basetype.boolean.checkString(value):
                value = j.basetype.boolean.fromString(value)
            else:
                msg="property async input error, needs to be bool, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_async=value

    @async.deleter
    def async(self):
        del self._P_async

    @property
    def period(self):
        return self._P_period

    @period.setter
    def period(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property period input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_period=value

    @period.deleter
    def period(self):
        del self._P_period

    @property
    def order(self):
        return self._P_order

    @order.setter
    def order(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property order input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_order=value

    @order.deleter
    def order(self):
        del self._P_order

    @property
    def queue(self):
        return self._P_queue

    @queue.setter
    def queue(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property queue input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_queue=value

    @queue.deleter
    def queue(self):
        del self._P_queue

    @property
    def log(self):
        return self._P_log

    @log.setter
    def log(self, value):
        if not isinstance(value, bool) and value is not None:
            if isinstance(value, basestring) and j.basetype.boolean.checkString(value):
                value = j.basetype.boolean.fromString(value)
            else:
                msg="property log input error, needs to be bool, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P_log=value

    @log.deleter
    def log(self):
        del self._P_log

    @property
    def guid(self):
        return self._P_guid

    @guid.setter
    def guid(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property guid input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
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
                msg="property _meta input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: jumpscript, value was:" + str(value)
                raise TypeError(msg)

        self._P__meta=value

    @_meta.deleter
    def _meta(self):
        del self._P__meta

