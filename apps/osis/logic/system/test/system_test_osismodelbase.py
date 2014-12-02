from JumpScale import j

class system_test_osismodelbase(j.code.classGetJSRootModelBase()):
    def __init__(self):
        pass
        self._P_id=0
        self._P_gid=0
        self._P_nid=0
        self._P_name=""
        self._P_testrun=""
        self._P_path=""
        self._P_state=""
        self._P_priority=0
        self._P_organization=""
        self._P_author=""
        self._P_version=0
        self._P_categories=list()
        self._P_starttime=0
        self._P_endtime=0
        self._P_enable=True
        self._P_result=dict()
        self._P_output=dict()
        self._P_eco=dict()
        self._P_license=""
        self._P_source=dict()
        self._P_guid=""
        self._P__meta=list()
        self._P__meta=["osismodel","system","test",1] #@todo version not implemented now, just already foreseen

    @property
    def id(self):
        return self._P_id

    @id.setter
    def id(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property id input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
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
                msg="property gid input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
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
                msg="property nid input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
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
                msg="property name input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_name=value

    @name.deleter
    def name(self):
        del self._P_name

    @property
    def testrun(self):
        return self._P_testrun

    @testrun.setter
    def testrun(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property testrun input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_testrun=value

    @testrun.deleter
    def testrun(self):
        del self._P_testrun

    @property
    def path(self):
        return self._P_path

    @path.setter
    def path(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property path input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_path=value

    @path.deleter
    def path(self):
        del self._P_path

    @property
    def state(self):
        return self._P_state

    @state.setter
    def state(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property state input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_state=value

    @state.deleter
    def state(self):
        del self._P_state

    @property
    def priority(self):
        return self._P_priority

    @priority.setter
    def priority(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property priority input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_priority=value

    @priority.deleter
    def priority(self):
        del self._P_priority

    @property
    def organization(self):
        return self._P_organization

    @organization.setter
    def organization(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property organization input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
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
                msg="property author input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_author=value

    @author.deleter
    def author(self):
        del self._P_author

    @property
    def version(self):
        return self._P_version

    @version.setter
    def version(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property version input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_version=value

    @version.deleter
    def version(self):
        del self._P_version

    @property
    def categories(self):
        return self._P_categories

    @categories.setter
    def categories(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property categories input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_categories=value

    @categories.deleter
    def categories(self):
        del self._P_categories

    @property
    def starttime(self):
        return self._P_starttime

    @starttime.setter
    def starttime(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property starttime input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_starttime=value

    @starttime.deleter
    def starttime(self):
        del self._P_starttime

    @property
    def endtime(self):
        return self._P_endtime

    @endtime.setter
    def endtime(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property endtime input error, needs to be int, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_endtime=value

    @endtime.deleter
    def endtime(self):
        del self._P_endtime

    @property
    def enable(self):
        return self._P_enable

    @enable.setter
    def enable(self, value):
        if not isinstance(value, bool) and value is not None:
            if isinstance(value, basestring) and j.basetype.boolean.checkString(value):
                value = j.basetype.boolean.fromString(value)
            else:
                msg="property enable input error, needs to be bool, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_enable=value

    @enable.deleter
    def enable(self):
        del self._P_enable

    @property
    def result(self):
        return self._P_result

    @result.setter
    def result(self, value):
        if not isinstance(value, dict) and value is not None:
            if isinstance(value, basestring) and j.basetype.dictionary.checkString(value):
                value = j.basetype.dictionary.fromString(value)
            else:
                msg="property result input error, needs to be dict, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_result=value

    @result.deleter
    def result(self):
        del self._P_result

    @property
    def output(self):
        return self._P_output

    @output.setter
    def output(self, value):
        if not isinstance(value, dict) and value is not None:
            if isinstance(value, basestring) and j.basetype.dictionary.checkString(value):
                value = j.basetype.dictionary.fromString(value)
            else:
                msg="property output input error, needs to be dict, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_output=value

    @output.deleter
    def output(self):
        del self._P_output

    @property
    def eco(self):
        return self._P_eco

    @eco.setter
    def eco(self, value):
        if not isinstance(value, dict) and value is not None:
            if isinstance(value, basestring) and j.basetype.dictionary.checkString(value):
                value = j.basetype.dictionary.fromString(value)
            else:
                msg="property eco input error, needs to be dict, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_eco=value

    @eco.deleter
    def eco(self):
        del self._P_eco

    @property
    def license(self):
        return self._P_license

    @license.setter
    def license(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property license input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_license=value

    @license.deleter
    def license(self):
        del self._P_license

    @property
    def source(self):
        return self._P_source

    @source.setter
    def source(self, value):
        if not isinstance(value, dict) and value is not None:
            if isinstance(value, basestring) and j.basetype.dictionary.checkString(value):
                value = j.basetype.dictionary.fromString(value)
            else:
                msg="property source input error, needs to be dict, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P_source=value

    @source.deleter
    def source(self):
        del self._P_source

    @property
    def guid(self):
        return self._P_guid

    @guid.setter
    def guid(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property guid input error, needs to be str, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
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
                msg="property _meta input error, needs to be list, specfile: /opt/jumpscale73/apps/osis/logic/system/model.spec, name model: test, value was:" + str(value)
                raise TypeError(msg)

        self._P__meta=value

    @_meta.deleter
    def _meta(self):
        del self._P__meta

