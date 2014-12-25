#every object has a guid
#because we are using mongodb best not to make nested structures
#every object also has an id = int they are both unique

[rootmodel:alert] @index
    prop:id int,,
    prop:gid int,,
    prop:nid int,,
    prop:description str,,
    prop:descriptionpub str,,
    prop:level int,, 1:critical, 2:warning, 3:info
    prop:category str,, dot notation e.g. machine.start.failed
    prop:tags str,, e.g. machine:2323
    prop:state str,, ["NEW","ALERT","CLOSED"]
    prop:inittime int,, first time there was an error condition linked to this alert
    prop:lasttime int,, last time there was an error condition linked to this alert
    prop:closetime int,, alert is closed, no longer active
    prop:nrerrorconditions int,, nr of times this error condition happened
    prop:errorconditions list(int),, ids of errorconditions

[rootmodel:audit]
    prop:id int,,
    prop:user str,,
    prop:result str,,
    prop:call str,,
    prop:statuscode str,,
    prop:args str,,
    prop:kwargs str,,
    prop:timestamp str,,

[rootmodel:disk] @index
    prop:id int,,
    prop:partnr int,,
    prop:gid int,,
    prop:nid int,,    
    prop:path str,,
    prop:size int,,
    prop:free int,,
    prop:ssd int,,
    prop:fs str,,
    prop:mounted bool,,
    prop:mountpoint str,,
    prop:active bool,,
    prop:model str,,
    prop:description str,,
    prop:type list(str),, BOOT, DATA, ...
    prop:lastcheck str,, epoch of last time the info was checked from reality

[rootmodel:eco] @index
    """
    Error Condition Object
    """
    prop:id int,,
    prop:gid int,,
    prop:nid int,,
    prop:aid int,,
    prop:pid int,,
    prop:jid int,,
    prop:masterjid int,,
    prop:epoch int,, epoch
    prop:appname str,, 
    prop:level int,, 1:critical, 2:warning, 3:info
    prop:type str,,
    prop:state str,, ["NEW","ALERT","CLOSED"]
    prop:errormessage str,, 
    prop:errormessagePub str,,
    prop:category str,, dot notation e.g. machine.start.failed
    prop:tags str,, e.g. machine:2323
    prop:code str,,
    prop:funcname str,,
    prop:funcfilename str,,
    prop:funclinenr int,,
    prop:backtrace str,,
    prop:backtraceDetailed str,,
    prop:extra str,,
    prop:lasttime int,, last time there was an error condition linked to this alert
    prop:closetime int,, alert is closed, no longer active
    prop:occurrences int,, nr of times this error condition happened

[rootmodel:grid] @index
    prop:id int,,    
    prop:name str,,
    prop:useavahi bool,,
    prop:nid int,,

[rootmodel:group] @index
    prop:id int,,    
    prop:domain str,,
    prop:gid int,,
    prop:roles list(str),,
    prop:active bool,,
    prop:description str,,
    prop:lastcheck int,, epoch of last time the info updated
    prop:users list(str),,

[rootmodel:heartbeat]
    """
    """
    prop:nid int,,
    prop:gid int,,
    prop:lastcheck int,,

[rootmodel:info] @index
    """
    """
    prop:nid int,,
    prop:gid int,,
    prop:category str,,
    prop:content str,,
    prop:epoch int,,

[model:job]
    """
    """
    prop:id int,,
    prop:sessionid int,,
    prop:nid int,,
    prop:gid int,,
    prop:cmd str,,
    prop:wait bool,,
    prop:category str,,
    prop:roles list(str),,
    prop:args str,,
    prop:queue str,,
    prop:timeout int,,
    prop:result str,,
    prop:parent int,,
    prop:resultcode str,,
    prop:state str,, SCHEDULED,STARTED,ERROR,OK,NOWORK
    prop:timeStart int,,
    prop:timeStop int,,
    prop:log bool,,
    prop:errorreport bool,,

[rootmodel:jumpscript] @index
    prop:id int,,    
    prop:gid int,,    
    prop:name str,,
    prop:descr str,,
    prop:category str,,
    prop:organization str,,
    prop:author str,,
    prop:license str,,
    prop:version str,,
    prop:roles list(str),,
    prop:action str,,
    prop:source str,,
    prop:path str,,
    prop:args list(str),,
    prop:enabled bool,,
    prop:async bool,,
    prop:period int,,
    prop:order int,,
    prop:queue str,,
    prop:log bool,,

[rootmodel:machine]
    prop:id int,,
    prop:gid int,,
    prop:nid int,,
    prop:name str,,
    prop:roles list(str),,
    prop:netaddr str,,
    prop:ipaddr list(str),,
    prop:active bool,,
    prop:state str,, STARTED,STOPPED,RUNNING,FROZEN,CONFIGURED,DELETED
    prop:mem int,, in MB
    prop:cpucore int,, 
    prop:description str,, 
    prop:otherid str,, 
    prop:type str,, VM,LXC
    prop:lastcheck int,, epoch of last time the info was checked from reality

[rootmodel:nic] @index
    """
    project
    """
    prop:id int,,
    prop:gid int,,
    prop:nid int,,
    prop:name str,,
    prop:mac str,,
    prop:ipaddr list(str),,
    prop:active bool,,
    prop:lastcheck int,, epoch of last time the info was checked from reality

[rootmodel:node]
    prop:id int,,
    prop:gid int,,
    prop:name str,,
    prop:roles list(str),,
    prop:netaddr str,,
    prop:machineguid str,,
    prop:ipaddr list(str),,
    prop:active bool,,
    prop:peer_stats int,, node which has stats for this node
    prop:peer_log int,, node which has transactionlog or other logs for this node
    prop:peer_backup int,, node which has backups for this node
    prop:description str,,
    prop:lastcheck int,,
    prop:_meta list(str),, osisrootobj,$namespace,$category,$version

[rootmodel:process] @index
    prop:id int,,
    prop:gid int,,
    prop:nid int,,
    prop:jpdomain str,,
    prop:jpname str,,
    prop:pname str,, process name
    prop:sname str,, name as specified in startup manager
    prop:ports list(int),,
    prop:instance str,,
    prop:systempid list(int),, system process id (PID) at this point
    prop:epochstart int,,
    prop:epochstop int,,
    prop:active bool,,
    prop:lastcheck int,,
    prop:cmd str,,
    prop:workingdir str,,
    prop:parent str,,
    prop:type str,,
    prop:statkey str,,
    prop:nr_file_descriptors float,,
    prop:nr_ctx_switches_voluntary float,,
    prop:nr_ctx_switches_involuntary float,,
    prop:nr_threads float,,
    prop:cpu_time_user float,,
    prop:cpu_time_system float,,
    prop:cpu_percent float,,
    prop:mem_vms float,,
    prop:mem_rss float,,
    prop:io_read_count float,,
    prop:io_write_count float,,
    prop:io_read_bytes float,,
    prop:io_write_bytes float,,
    prop:nr_connections_in float,,
    prop:nr_connections_out float,,

[rootmodel:test] @index
    """
    """
    prop:id int,,
    prop:gid int,,
    prop:nid int,,
    prop:name str,,
    prop:testrun str,, 
    prop:path str,,
    prop:state str,, #OK, ERROR, DISABLED
    prop:priority int,, #lower is highest priority
    prop:organization str,,
    prop:author str,,
    prop:version int,,
    prop:categories list(str),,
    prop:starttime int,,
    prop:endtime int,,
    prop:enable bool,,
    prop:result dict(str),,
    prop:output dict(str),,
    prop:eco dict(str),,
    prop:license str,,
    prop:source dict(str),,

[rootmodel:user] @index
    """
    """
    prop:id int,,
    prop:domain str,,
    prop:gid int,,
    prop:passwd str,, #stored hashed
    prop:roles list(str),,
    prop:active bool,,
    prop:description str,,
    prop:emails list(str),,
    prop:xmpp list(str),,
    prop:mobile list(str),,
    prop:lastcheck int,, #epoch of last time the info updated
    prop:groups list(str),,
    prop:authkey str,,
    prop:data str,,
    prop:authkeys list(str),,

[rootmodel:vdisk] @index
    prop:id int,,
    prop:gid int,,
    prop:nid int,,
    prop:path str,,
    prop:backingpath str,,
    prop:size int,, #KB
    prop:free int,, #KB
    prop:sizeondisk int,, #size on physical disk after e.g. compression ... KB
    prop:fs str,,
    prop:active bool,,
    prop:description str,,
    prop:role str,,  #BOOT,DATA,...
    prop:machineid int,,  #who is using it
    prop:order int,,
    prop:type str,, #QCOW2,FS
    prop:backup bool,,
    prop:backuptime int,,
    prop:expiration int,,
    prop:backuplocation str,, #where is backup stored (tag based notation)
    prop:devicename str,,
    prop:lastcheck int,, #epoch of last time the info was checked from reality
