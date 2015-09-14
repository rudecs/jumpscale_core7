from app.sqlalchemy.common import CommonColumns, typemap
import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    ForeignKey,
    DateTime)



class audit(CommonColumns):
    __tablename__ = 'audit'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    user = Column(typemap['str'])
    result = Column(typemap['str'])
    call = Column(typemap['str'])
    statuscode = Column(typemap['str'])
    args = Column(typemap['str'])
    kwargs = Column(typemap['str'])
    timestamp = Column(typemap['str'])


class info(CommonColumns):
    __tablename__ = 'info'
    guid = Column(String(36), primary_key=True)

    nid = Column(typemap['int'])
    gid = Column(typemap['int'])
    category = Column(typemap['str'])
    content = Column(typemap['str'])
    epoch = Column(typemap['int'])
    id = Column(typemap['int'])


class group(CommonColumns):
    __tablename__ = 'group'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    domain = Column(typemap['str'])
    gid = Column(typemap['int'])
    roles = Column(typemap['list'])
    active = Column(typemap['bool'])
    description = Column(typemap['str'])
    lastcheck = Column(typemap['int'])
    users = Column(typemap['list'])


class jumpscript(CommonColumns):
    __tablename__ = 'jumpscript'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    gid = Column(typemap['int'])
    name = Column(typemap['str'])
    descr = Column(typemap['str'])
    category = Column(typemap['str'])
    organization = Column(typemap['str'])
    author = Column(typemap['str'])
    license = Column(typemap['str'])
    version = Column(typemap['str'])
    roles = Column(typemap['list'])
    action = Column(typemap['str'])
    source = Column(typemap['str'])
    path = Column(typemap['str'])
    args = Column(typemap['list'])
    enabled = Column(typemap['bool'])
    async = Column(typemap['bool'])
    period = Column(typemap['int'])
    order = Column(typemap['int'])
    queue = Column(typemap['str'])
    log = Column(typemap['bool'])


class eco(CommonColumns):
    __tablename__ = 'eco'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    gid = Column(typemap['int'])
    nid = Column(typemap['int'])
    aid = Column(typemap['int'])
    pid = Column(typemap['int'])
    jid = Column(typemap['int'])
    masterjid = Column(typemap['int'])
    epoch = Column(typemap['int'])
    appname = Column(typemap['str'])
    level = Column(typemap['int'])
    type = Column(typemap['str'])
    state = Column(typemap['str'])
    errormessage = Column(typemap['str'])
    errormessagePub = Column(typemap['str'])
    category = Column(typemap['str'])
    tags = Column(typemap['str'])
    code = Column(typemap['str'])
    funcname = Column(typemap['str'])
    funcfilename = Column(typemap['str'])
    funclinenr = Column(typemap['int'])
    backtrace = Column(typemap['str'])
    backtraceDetailed = Column(typemap['str'])
    extra = Column(typemap['str'])
    lasttime = Column(typemap['int'])
    closetime = Column(typemap['int'])
    occurrences = Column(typemap['int'])


class nic(CommonColumns):
    __tablename__ = 'nic'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    gid = Column(typemap['int'])
    nid = Column(typemap['int'])
    name = Column(typemap['str'])
    mac = Column(typemap['str'])
    ipaddr = Column(typemap['list'])
    active = Column(typemap['bool'])
    lastcheck = Column(typemap['int'])


class node(CommonColumns):
    __tablename__ = 'node'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    gid = Column(typemap['int'])
    name = Column(typemap['str'])
    roles = Column(typemap['list'])
    netaddr = Column(typemap['str'])
    machineguid = Column(typemap['str'])
    ipaddr = Column(typemap['list'])
    active = Column(typemap['bool'])
    peer_stats = Column(typemap['int'])
    peer_log = Column(typemap['int'])
    peer_backup = Column(typemap['int'])
    description = Column(typemap['str'])
    lastcheck = Column(typemap['int'])
    _meta = Column(typemap['list'])


class alert(CommonColumns):
    __tablename__ = 'alert'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    gid = Column(typemap['int'])
    nid = Column(typemap['int'])
    description = Column(typemap['str'])
    descriptionpub = Column(typemap['str'])
    level = Column(typemap['int'])
    category = Column(typemap['str'])
    tags = Column(typemap['str'])
    state = Column(typemap['str'])
    inittime = Column(typemap['int'])
    lasttime = Column(typemap['int'])
    closetime = Column(typemap['int'])
    nrerrorconditions = Column(typemap['int'])
    errorconditions = Column(typemap['list'])


class machine(CommonColumns):
    __tablename__ = 'machine'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    gid = Column(typemap['int'])
    nid = Column(typemap['int'])
    name = Column(typemap['str'])
    roles = Column(typemap['list'])
    netaddr = Column(typemap['str'])
    ipaddr = Column(typemap['list'])
    active = Column(typemap['bool'])
    state = Column(typemap['str'])
    mem = Column(typemap['int'])
    cpucore = Column(typemap['int'])
    description = Column(typemap['str'])
    otherid = Column(typemap['str'])
    type = Column(typemap['str'])
    lastcheck = Column(typemap['int'])


class process(CommonColumns):
    __tablename__ = 'process'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    gid = Column(typemap['int'])
    nid = Column(typemap['int'])
    aysdomain = Column(typemap['str'])
    aysname = Column(typemap['str'])
    pname = Column(typemap['str'])
    sname = Column(typemap['str'])
    ports = Column(typemap['list'])
    instance = Column(typemap['str'])
    systempid = Column(typemap['list'])
    epochstart = Column(typemap['int'])
    epochstop = Column(typemap['int'])
    active = Column(typemap['bool'])
    lastcheck = Column(typemap['int'])
    cmd = Column(typemap['str'])
    workingdir = Column(typemap['str'])
    parent = Column(typemap['str'])
    type = Column(typemap['str'])
    statkey = Column(typemap['str'])
    nr_file_descriptors = Column(typemap['float'])
    nr_ctx_switches_voluntary = Column(typemap['float'])
    nr_ctx_switches_involuntary = Column(typemap['float'])
    nr_threads = Column(typemap['float'])
    cpu_time_user = Column(typemap['float'])
    cpu_time_system = Column(typemap['float'])
    cpu_percent = Column(typemap['float'])
    mem_vms = Column(typemap['float'])
    mem_rss = Column(typemap['float'])
    io_read_count = Column(typemap['float'])
    io_write_count = Column(typemap['float'])
    io_read_bytes = Column(typemap['float'])
    io_write_bytes = Column(typemap['float'])
    nr_connections_in = Column(typemap['float'])
    nr_connections_out = Column(typemap['float'])


class grid(CommonColumns):
    __tablename__ = 'grid'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    name = Column(typemap['str'])
    useavahi = Column(typemap['bool'])
    nid = Column(typemap['int'])


class user(CommonColumns):
    __tablename__ = 'user'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['str'])
    domain = Column(typemap['str'])
    gid = Column(typemap['int'])
    passwd = Column(typemap['str'])
    roles = Column(typemap['list'])
    active = Column(typemap['bool'])
    description = Column(typemap['str'])
    emails = Column(typemap['list'])
    xmpp = Column(typemap['list'])
    mobile = Column(typemap['list'])
    lastcheck = Column(typemap['int'])
    groups = Column(typemap['list'])
    authkey = Column(typemap['str'])
    data = Column(typemap['str'])
    authkeys = Column(typemap['list'])


class test(CommonColumns):
    __tablename__ = 'test'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    gid = Column(typemap['int'])
    nid = Column(typemap['int'])
    name = Column(typemap['str'])
    testrun = Column(typemap['str'])
    path = Column(typemap['str'])
    state = Column(typemap['str'])
    priority = Column(typemap['int'])
    organization = Column(typemap['str'])
    author = Column(typemap['str'])
    version = Column(typemap['int'])
    categories = Column(typemap['list'])
    starttime = Column(typemap['int'])
    endtime = Column(typemap['int'])
    enable = Column(typemap['bool'])
    result = Column(typemap['dict'])
    output = Column(typemap['dict'])
    eco = Column(typemap['dict'])
    license = Column(typemap['str'])
    source = Column(typemap['dict'])


class heartbeat(CommonColumns):
    __tablename__ = 'heartbeat'
    guid = Column(String(36), primary_key=True)

    nid = Column(typemap['int'])
    gid = Column(typemap['int'])
    lastcheck = Column(typemap['int'])
    id = Column(typemap['int'])


class disk(CommonColumns):
    __tablename__ = 'disk'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    partnr = Column(typemap['int'])
    gid = Column(typemap['int'])
    nid = Column(typemap['int'])
    path = Column(typemap['str'])
    size = Column(typemap['int'])
    free = Column(typemap['int'])
    ssd = Column(typemap['int'])
    fs = Column(typemap['str'])
    mounted = Column(typemap['bool'])
    mountpoint = Column(typemap['str'])
    active = Column(typemap['bool'])
    model = Column(typemap['str'])
    description = Column(typemap['str'])
    type = Column(typemap['list'])
    lastcheck = Column(typemap['str'])


class vdisk(CommonColumns):
    __tablename__ = 'vdisk'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['int'])
    gid = Column(typemap['int'])
    nid = Column(typemap['int'])
    path = Column(typemap['str'])
    backingpath = Column(typemap['str'])
    size = Column(typemap['int'])
    free = Column(typemap['int'])
    sizeondisk = Column(typemap['int'])
    fs = Column(typemap['str'])
    active = Column(typemap['bool'])
    description = Column(typemap['str'])
    role = Column(typemap['str'])
    machineid = Column(typemap['int'])
    order = Column(typemap['int'])
    type = Column(typemap['str'])
    backup = Column(typemap['bool'])
    backuptime = Column(typemap['int'])
    expiration = Column(typemap['int'])
    backuplocation = Column(typemap['str'])
    devicename = Column(typemap['str'])
    lastcheck = Column(typemap['int'])
