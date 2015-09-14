from JumpScale import j

class system_process_osismodelbase(j.code.classGetJSRootModelBase()):
    def __init__(self):
        pass
        self._P_id=0
        self._P_gid=0
        self._P_nid=0
        self._P_aysdomain=""
        self._P_aysname=""
        self._P_pname=""
        self._P_sname=""
        self._P_ports=list()
        self._P_instance=""
        self._P_systempid=list()
        self._P_epochstart=0
        self._P_epochstop=0
        self._P_active=True
        self._P_lastcheck=0
        self._P_cmd=""
        self._P_workingdir=""
        self._P_parent=""
        self._P_type=""
        self._P_statkey=""
        self._P_nr_file_descriptors=0.0
        self._P_nr_ctx_switches_voluntary=0.0
        self._P_nr_ctx_switches_involuntary=0.0
        self._P_nr_threads=0.0
        self._P_cpu_time_user=0.0
        self._P_cpu_time_system=0.0
        self._P_cpu_percent=0.0
        self._P_mem_vms=0.0
        self._P_mem_rss=0.0
        self._P_io_read_count=0.0
        self._P_io_write_count=0.0
        self._P_io_read_bytes=0.0
        self._P_io_write_bytes=0.0
        self._P_nr_connections_in=0.0
        self._P_nr_connections_out=0.0
        self._P_guid=""
        self._P__meta=list()
        self._P__meta=["osismodel","system","process",1] #@todo version not implemented now, just already foreseen

    @property
    def id(self):
        return self._P_id

    @id.setter
    def id(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property id input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
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
                msg="property gid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
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
                msg="property nid input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_nid=value

    @nid.deleter
    def nid(self):
        del self._P_nid

    @property
    def aysdomain(self):
        return self._P_aysdomain

    @aysdomain.setter
    def aysdomain(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property aysdomain input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_aysdomain=value

    @aysdomain.deleter
    def aysdomain(self):
        del self._P_aysdomain

    @property
    def aysname(self):
        return self._P_aysname

    @aysname.setter
    def aysname(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property aysname input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_aysname=value

    @aysname.deleter
    def aysname(self):
        del self._P_aysname

    @property
    def pname(self):
        return self._P_pname

    @pname.setter
    def pname(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property pname input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_pname=value

    @pname.deleter
    def pname(self):
        del self._P_pname

    @property
    def sname(self):
        return self._P_sname

    @sname.setter
    def sname(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property sname input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_sname=value

    @sname.deleter
    def sname(self):
        del self._P_sname

    @property
    def ports(self):
        return self._P_ports

    @ports.setter
    def ports(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property ports input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_ports=value

    @ports.deleter
    def ports(self):
        del self._P_ports

    @property
    def instance(self):
        return self._P_instance

    @instance.setter
    def instance(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property instance input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_instance=value

    @instance.deleter
    def instance(self):
        del self._P_instance

    @property
    def systempid(self):
        return self._P_systempid

    @systempid.setter
    def systempid(self, value):
        if not isinstance(value, list) and value is not None:
            if isinstance(value, basestring) and j.basetype.list.checkString(value):
                value = j.basetype.list.fromString(value)
            else:
                msg="property systempid input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_systempid=value

    @systempid.deleter
    def systempid(self):
        del self._P_systempid

    @property
    def epochstart(self):
        return self._P_epochstart

    @epochstart.setter
    def epochstart(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property epochstart input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_epochstart=value

    @epochstart.deleter
    def epochstart(self):
        del self._P_epochstart

    @property
    def epochstop(self):
        return self._P_epochstop

    @epochstop.setter
    def epochstop(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property epochstop input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_epochstop=value

    @epochstop.deleter
    def epochstop(self):
        del self._P_epochstop

    @property
    def active(self):
        return self._P_active

    @active.setter
    def active(self, value):
        if not isinstance(value, bool) and value is not None:
            if isinstance(value, basestring) and j.basetype.boolean.checkString(value):
                value = j.basetype.boolean.fromString(value)
            else:
                msg="property active input error, needs to be bool, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_active=value

    @active.deleter
    def active(self):
        del self._P_active

    @property
    def lastcheck(self):
        return self._P_lastcheck

    @lastcheck.setter
    def lastcheck(self, value):
        if not isinstance(value, int) and value is not None:
            if isinstance(value, basestring) and j.basetype.integer.checkString(value):
                value = j.basetype.integer.fromString(value)
            else:
                msg="property lastcheck input error, needs to be int, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_lastcheck=value

    @lastcheck.deleter
    def lastcheck(self):
        del self._P_lastcheck

    @property
    def cmd(self):
        return self._P_cmd

    @cmd.setter
    def cmd(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property cmd input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_cmd=value

    @cmd.deleter
    def cmd(self):
        del self._P_cmd

    @property
    def workingdir(self):
        return self._P_workingdir

    @workingdir.setter
    def workingdir(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property workingdir input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_workingdir=value

    @workingdir.deleter
    def workingdir(self):
        del self._P_workingdir

    @property
    def parent(self):
        return self._P_parent

    @parent.setter
    def parent(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property parent input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_parent=value

    @parent.deleter
    def parent(self):
        del self._P_parent

    @property
    def type(self):
        return self._P_type

    @type.setter
    def type(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property type input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_type=value

    @type.deleter
    def type(self):
        del self._P_type

    @property
    def statkey(self):
        return self._P_statkey

    @statkey.setter
    def statkey(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property statkey input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_statkey=value

    @statkey.deleter
    def statkey(self):
        del self._P_statkey

    @property
    def nr_file_descriptors(self):
        return self._P_nr_file_descriptors

    @nr_file_descriptors.setter
    def nr_file_descriptors(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property nr_file_descriptors input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_nr_file_descriptors=value

    @nr_file_descriptors.deleter
    def nr_file_descriptors(self):
        del self._P_nr_file_descriptors

    @property
    def nr_ctx_switches_voluntary(self):
        return self._P_nr_ctx_switches_voluntary

    @nr_ctx_switches_voluntary.setter
    def nr_ctx_switches_voluntary(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property nr_ctx_switches_voluntary input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_nr_ctx_switches_voluntary=value

    @nr_ctx_switches_voluntary.deleter
    def nr_ctx_switches_voluntary(self):
        del self._P_nr_ctx_switches_voluntary

    @property
    def nr_ctx_switches_involuntary(self):
        return self._P_nr_ctx_switches_involuntary

    @nr_ctx_switches_involuntary.setter
    def nr_ctx_switches_involuntary(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property nr_ctx_switches_involuntary input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_nr_ctx_switches_involuntary=value

    @nr_ctx_switches_involuntary.deleter
    def nr_ctx_switches_involuntary(self):
        del self._P_nr_ctx_switches_involuntary

    @property
    def nr_threads(self):
        return self._P_nr_threads

    @nr_threads.setter
    def nr_threads(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property nr_threads input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_nr_threads=value

    @nr_threads.deleter
    def nr_threads(self):
        del self._P_nr_threads

    @property
    def cpu_time_user(self):
        return self._P_cpu_time_user

    @cpu_time_user.setter
    def cpu_time_user(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property cpu_time_user input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_cpu_time_user=value

    @cpu_time_user.deleter
    def cpu_time_user(self):
        del self._P_cpu_time_user

    @property
    def cpu_time_system(self):
        return self._P_cpu_time_system

    @cpu_time_system.setter
    def cpu_time_system(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property cpu_time_system input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_cpu_time_system=value

    @cpu_time_system.deleter
    def cpu_time_system(self):
        del self._P_cpu_time_system

    @property
    def cpu_percent(self):
        return self._P_cpu_percent

    @cpu_percent.setter
    def cpu_percent(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property cpu_percent input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_cpu_percent=value

    @cpu_percent.deleter
    def cpu_percent(self):
        del self._P_cpu_percent

    @property
    def mem_vms(self):
        return self._P_mem_vms

    @mem_vms.setter
    def mem_vms(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property mem_vms input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_mem_vms=value

    @mem_vms.deleter
    def mem_vms(self):
        del self._P_mem_vms

    @property
    def mem_rss(self):
        return self._P_mem_rss

    @mem_rss.setter
    def mem_rss(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property mem_rss input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_mem_rss=value

    @mem_rss.deleter
    def mem_rss(self):
        del self._P_mem_rss

    @property
    def io_read_count(self):
        return self._P_io_read_count

    @io_read_count.setter
    def io_read_count(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property io_read_count input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_io_read_count=value

    @io_read_count.deleter
    def io_read_count(self):
        del self._P_io_read_count

    @property
    def io_write_count(self):
        return self._P_io_write_count

    @io_write_count.setter
    def io_write_count(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property io_write_count input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_io_write_count=value

    @io_write_count.deleter
    def io_write_count(self):
        del self._P_io_write_count

    @property
    def io_read_bytes(self):
        return self._P_io_read_bytes

    @io_read_bytes.setter
    def io_read_bytes(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property io_read_bytes input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_io_read_bytes=value

    @io_read_bytes.deleter
    def io_read_bytes(self):
        del self._P_io_read_bytes

    @property
    def io_write_bytes(self):
        return self._P_io_write_bytes

    @io_write_bytes.setter
    def io_write_bytes(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property io_write_bytes input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_io_write_bytes=value

    @io_write_bytes.deleter
    def io_write_bytes(self):
        del self._P_io_write_bytes

    @property
    def nr_connections_in(self):
        return self._P_nr_connections_in

    @nr_connections_in.setter
    def nr_connections_in(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property nr_connections_in input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_nr_connections_in=value

    @nr_connections_in.deleter
    def nr_connections_in(self):
        del self._P_nr_connections_in

    @property
    def nr_connections_out(self):
        return self._P_nr_connections_out

    @nr_connections_out.setter
    def nr_connections_out(self, value):
        if not isinstance(value, float) and value is not None:
            if isinstance(value, basestring) and j.basetype.float.checkString(value):
                value = j.basetype.float.fromString(value)
            else:
                msg="property nr_connections_out input error, needs to be float, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P_nr_connections_out=value

    @nr_connections_out.deleter
    def nr_connections_out(self):
        del self._P_nr_connections_out

    @property
    def guid(self):
        return self._P_guid

    @guid.setter
    def guid(self, value):
        if not isinstance(value, str) and value is not None:
            if isinstance(value, basestring) and j.basetype.string.checkString(value):
                value = j.basetype.string.fromString(value)
            else:
                msg="property guid input error, needs to be str, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
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
                msg="property _meta input error, needs to be list, specfile: /opt/jumpscale7/apps/osis/logic/system/model.spec, name model: process, value was:" + str(value)
                raise TypeError(msg)

        self._P__meta=value

    @_meta.deleter
    def _meta(self):
        del self._P__meta

