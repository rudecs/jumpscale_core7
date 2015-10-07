import shlex
import json
import re
import inspect
from StringIO import StringIO

import acclient


STATE_UNKNOWN = 'UNKNOWN'
STATE_SUCCESS = 'SUCCESS'
STATE_TIMEDOUT = 'TIMEDOUT'

RESULT_JSON = 20


class Agent(object):
    def __init__(self, client, gid, nid, roles):
        self._client = client
        self._gid = gid
        self._nid = nid
        self._roles = roles
        self._os_info = None
        self._nic_info = None
        self._aggr_stats = None

    def _get_os_info(self):
        if self._os_info is None:
            self._os_info = self._client.get_os_info(self.gid, self.nid)

        return self._os_info

    def _get_nic_info(self):
        if self._nic_info is None:
            self._nic_info = self._client.get_nic_info(self.gid, self.nid)

        return self._nic_info

    def _get_aggregated_stats(self, update=False):
        if self._aggr_stats is None or update:
            self._aggr_stats = self._client.get_aggregated_stats(self.gid, self.nid)

        return self._aggr_stats

    @property
    def gid(self):
        return self._gid

    @property
    def nid(self):
        return self._nid

    @property
    def roles(self):
        return self._roles

    @property
    def hostname(self):
        return self._get_os_info()['hostname']

    @property
    def cpu(self):
        """
        Gets CPU percentage of agent (with sub processes)
        """
        return self._get_aggregated_stats(True)['cpu']

    @property
    def mem(self):
        """
        Gets the agent VMS (with sub processes)
        """
        return self._get_aggregated_stats(True)['vms']

    @property
    def macaddr(self):
        nics = self._get_nic_info()
        return dict([(nic['name'], nic['hardwareaddr']) for nic in nics])

    @property
    def ipaddr(self):
        nics = self._get_nic_info()
        addrr = {}
        for nic in nics:
            nic_addr = map(lambda a: a['addr'], nic['addrs'])
            addrr[nic['name']] = nic_addr

        return addrr

    def __repr__(self):
        return '<Agent {this.gid}:{this.nid} {this.roles}>'.format(this=self)


class Result(object):
    def __init__(self, job):
        self._job = job

    @property
    def state(self):
        return self._job.state

    @property
    def gid(self):
        return self._job.gid

    @property
    def nid(self):
        return self._job.nid

    @property
    def result(self):
        if self.state != STATE_SUCCESS:
            raise ValueError("Job in %s" % self.state)
        if self._job.level == RESULT_JSON:
            return json.loads(self._job.data)

    @property
    def error(self):
        if self.state != STATE_SUCCESS:
            return self._job.streams[1] or self._job.data

    # def get_losg(self):

    def __repr__(self):
        return '<Result {this.state} from {this.gid}:{this.nid}>'.format(this=self)


class Peer(object):
    def __init__(self, gid, nid, peer, share):
        self._gid = gid
        self._nid = nid
        self._peer = peer
        self._share = share
        self._sync_client = share._sync_client

    @property
    def gid(self):
        return self._gid

    @property
    def nid(self):
        return self._nid

    @property
    def insync(self):
        need = self._sync_client._get_need(self.gid, self.nid, self._share.name)
        if need['progress'] or need['queued'] or need['rest']:
            return False
        else:
            return True

    def __repr__(self):
        return '<Peer {this.gid}:{this.nid}>'.format(this=self)


class Share(object):
    def __init__(self, gid, nid, folder, sync_client):
        self._gid = gid
        self._nid = nid
        self._folder = folder
        self._sync_client = sync_client
        self._ignore = None

    @property
    def gid(self):
        return self._gid

    @property
    def nid(self):
        return self._nid

    @property
    def name(self):
        return self._folder['id']

    @property
    def path(self):
        return self._folder['path']

    @property
    def peers(self):
        peers = self._sync_client._get_devices(self.gid, self.nid)
        share_peers = []
        for share_peer in self._folder['devices']:
            device_id = share_peer['deviceID']
            if device_id not in peers:
                continue

            peer = peers[device_id]
            name = peer['name']
            # name should contain the gid-nid info.
            m = re.match('^(\d+)-(\d+)$', name)
            if not m:
                # not added via the API
                continue

            gid = int(m.group(1))
            nid = int(m.group(2))

            share_peers.append(Peer(gid, nid, peer, self))

        return share_peers

    @property
    def insync(self):
        for peer in self.peers:
            if not peer.insync:
                return False
        return True

    @property
    def ignore(self):
        if self._ignore is None:
            self._ignore = self._sync_client._get_ingore(self.gid, self.nid, self.path)

        return self._ignore

    def attach(self, gid, nid, path):
        remote_id = self._sync_client._get_id(gid, nid)
        self._sync_client._add_device(self.gid, self.nid, '%d-%d' % (gid, nid), remote_id)
        self._sync_client._add_device_to_share(self.gid, self.nid, remote_id, self.name)

        self._sync_client.create_share(gid, nid, self.name, path, readonly=False)
        local_id = self._sync_client._get_id(self.gid, self.nid)

        self._sync_client._add_device(gid, nid, '%d-%d' % (self.gid, self.nid), local_id)
        # TODO: the next call for some reason causes syncthing to exit.
        # self._sync_client._add_device_to_share(gid, nid, local_id, self.name)

    def __repr__(self):
        return '<Share on {this.gid}:{this.nid} {this.path}>'.format(this=self)


class SyncClient(object):
    API_TIMEOUT = 10

    def __init__(self, advanced_client):
        self._client = advanced_client
        self._ids_cache = {}

    def _get_id(self, gid, nid):
        if (gid, nid) in self._ids_cache:
            return self._ids_cache[(gid, nid)]

        runargs = acclient.RunArgs(name='get_id', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(gid, nid, 'sync', args=runargs)
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        id = self._client._load_json_or_die(job)

        self._ids_cache[(gid, nid)] = id
        return id

    def _get_ingore(self, gid, nid, path):
        runargs = acclient.RunArgs(name='get_share_ignore', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(gid, nid, 'sync', args=runargs, data=json.dumps({'path': path}))
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        return self._client._load_json_or_die(job).get('ignore', []) or []

    def _get_devices(self, gid, nid):
        runargs = acclient.RunArgs(name='list_devices', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(gid, nid, 'sync', args=runargs)
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        devices = self._client._load_json_or_die(job)
        return dict(map(lambda d: (d['deviceID'], d), devices))

    def _get_need(self, gid, nid, folder_id):
        runargs = acclient.RunArgs(name='get_share_need', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(gid, nid, 'sync', args=runargs, data=json.dumps({'name': folder_id}))
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        return self._client._load_json_or_die(job)

    def _add_device(self, gid, nid, name, id):
        data = {
            'name': name,
            'id': id
        }

        runargs = acclient.RunArgs(name='add_device', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(gid, nid, 'sync', args=runargs, data=json.dumps(data))
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        folder = self._client._load_json_or_die(job)
        return Share(gid, nid, folder, self)

    def _add_device_to_share(self, gid, nid, device_id, folder_id):
        data = {
            'device_id': device_id,
            'folder_id': folder_id
        }

        runargs = acclient.RunArgs(name='add_device_to_share', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(gid, nid, 'sync', args=runargs, data=json.dumps(data))
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        return self._client._load_json_or_die(job)

    def create_share(self, gid, nid, name, path, readonly=True, ignore=[]):
        data = {
            'path': path,
            'readonly': readonly,
            'ignore': ignore,
            'name': name
        }

        runargs = acclient.RunArgs(name='create_share', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(gid, nid, 'sync', args=runargs, data=json.dumps(data))
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        folder = self._client._load_json_or_die(job)
        return Share(gid, nid, folder, self)

    def list_shares(self, gid, nid):
        runargs = acclient.RunArgs(name='list_shares', max_time=SyncClient.API_TIMEOUT)
        command = self._client.cmd(gid, nid, 'sync', args=runargs)
        job = command.get_next_result(SyncClient.API_TIMEOUT)
        return map(lambda folder: Share(gid, nid, folder, self), self._client._load_json_or_die(job))


class SimpleClient(object):
    def __init__(self, advanced_client):
        self._client = advanced_client
        self._sync = SyncClient(advanced_client)

    @property
    def sync(self):
        return self._sync

    def getAgents(self):
        cmd = self._client.cmd(None, None, 'controller', acclient.RunArgs(name='list_agents'), roles=['*'])
        job = cmd.get_next_result()

        agents = self._client._load_json_or_die(job)
        results = []
        for key, roles in agents.iteritems():
            gid, _, nid = key.partition(':')
            results.append(Agent(self._client, int(gid), int(nid), roles))

        return results

    def _build_result(self, results):
        buff = StringIO()
        for gid, nid, state, stdout, stderr in results:
            buff.write('$agent (%d,%d)\n' % (gid, nid))
            buff.write(stdout)
            buff.write('\n')
            if state != STATE_SUCCESS:
                buff.write('##RC: %s\n' % state)
                buff.write('##ERROR:\n%s\n' % stderr)

            buff.write('#######################################################\n\n')
        return buff.getvalue()

    def _process_exec_jobs(self, cmd, die, timeout, fanout):
        jobs = []
        for job in cmd.get_jobs().itervalues():
            state = STATE_UNKNOWN
            try:
                job.wait(timeout)
                state = job.state
            except acclient.ResultTimeout:
                if die:
                    raise
                state = STATE_TIMEDOUT

            stdout, stderr = job.streams
            error = stderr or job.data
            if state != STATE_SUCCESS and die:
                raise acclient.AgentException(
                    'Job on agent {job.gid}.{job.nid} failed with status: "{job.state}" and message: "{error}"'.format(
                        job=job, error=error)
                )

            jobs.append((job.gid, job.nid, state, stdout, error))

        if fanout:
            # potential multiple results.
            return self._build_result(jobs)
        else:
            # single job
            _, _, state, stdout, stderr = jobs.pop()
            return state, stdout, stderr

    def execute(self, cmd, path=None, gid=None, nid=None, roles=[], fanout=False, die=True, timeout=5, data=None):
        parts = shlex.split(cmd)
        assert len(parts) > 0, "Empty command string"
        cmd = parts[0]
        args = parts[1:]

        if nid is None and not roles:
            roles = ['*']

        runargs = acclient.RunArgs(max_time=timeout, working_dir=path)
        command = self._client.execute(gid, nid, cmd, cmdargs=args, args=runargs, data=data, roles=roles, fanout=fanout)

        return self._process_exec_jobs(command, die, timeout, fanout)

    def executeBash(self, cmds, path=None, gid=None, nid=None, roles=[], fanout=False, die=True, timeout=5):
        if nid is None and not roles:
            roles = ['*']

        runargs = acclient.RunArgs(max_time=timeout, working_dir=path)
        command = self._client.cmd(gid, nid, 'bash', args=runargs, data=cmds, roles=roles, fanout=fanout)

        return self._process_exec_jobs(command, die, timeout, fanout)

    def _getFuncCode(self, func):
        if not inspect.isfunction(func):
            raise ValueError('method must be function (not class method)')

        source = inspect.getsource(func)
        if func.func_name != 'action':
            source = re.sub('^def\s+%s\(' % func.func_name, 'def action(', source, 1)
        return source

    def executeJumpscript(self, domain=None, name=None, content=None, path=None, method=None,
                          gid=None, nid=None, roles=[], fanout=False, die=True, timeout=5, args={}):
        jobs = self.executeJumpscriptAsync(
            domain=domain, name=name, content=content, path=path, method=method,
            gid=gid, nid=nid, roles=roles, fanout=fanout, die=die, timeout=timeout, args=args
        )

        results = []
        for job in jobs:
            state = STATE_UNKNOWN
            try:
                job.wait(timeout)
                state = job.state
            except acclient.ResultTimeout:
                if die:
                    raise
                state = STATE_TIMEDOUT

            if state != STATE_SUCCESS and die:
                stderr = job.streams[1]
                error = stderr or job.data
                raise acclient.AgentException(
                    'Job on agent {job.gid}.{job.nid} failed with status: "{job.state}" and message: "{error}"'.format(
                        job=job, error=error)
                )

            results.append(Result(job))

        return results

    def executeJumpscriptAsync(self, domain=None, name=None, content=None, path=None, method=None,
                               gid=None, nid=None, roles=[], fanout=False, die=True, timeout=5, args={}):
        if nid is None and not roles:
            roles = ['*']

        if domain is not None:
            assert name is not None, "name is required in case 'domain' is given"
        else:
            if not content and not path and not method:
                raise ValueError('domain/name, content, or path must be supplied')

        runargs = acclient.RunArgs(max_time=timeout)
        if domain is not None:
            command = self._client.execute_jumpscript(gid=gid, nid=nid, domain=domain, name=name,
                                                      args=args, runargs=runargs, roles=roles, fanout=fanout)
        else:
            # call the unexposed jumpscript_content extension manually
            runargs = runargs.update({'name': path})
            if method:
                content = self._getFuncCode(method)
            data = {
                'content': content,
                'args': args
            }
            command = self._client.cmd(gid=gid, nid=nid, cmd='jumpscript_content', args=runargs,
                                       data=json.dumps(data), roles=roles, fanout=fanout)

        return command.get_jobs().values()

    def tunnel_create(self, gid, nid, local, remote_gid, remote_nid, ip, remote):
        """
        Opens a tunnel that accepts connection at the agent's local port `local`
        and forwards the received connections to remote agent `gateway` which will
        forward the tunnel connection to `ip:remote`

        Note: The agent will proxy the connection over the agent-controller it recieved this open command from.

        :param gid: Grid id
        :param nid: Node id
        :param local: Agent's local listening port for the tunnel. 0 for dynamic allocation
        :param gateway: The other endpoint `agent` which the connection will be redirected to.
                      This should be the name of the hubble agent.
                      NOTE: if the endpoint is another superangent, it automatically names itself as '<gid>.<nid>'
        :param ip: The endpoint ip address on the remote agent network. Note that IP must be a real ip not a host name
                 dns names lookup is not supported.
        :param remote: The endpoint port on the remote agent network
        """

        agents = self.getAgents()
        found = False
        for agent in agents:
            if agent.nid == remote_nid and agent.gid == remote_gid:
                found = True
                break

        if not found:
            raise acclient.AgentException('Remote end %s:%s is not alive!' % (remote_gid, remote_nid))

        gateway = '%s.%s' % (remote_gid, remote_nid)
        return self._client.tunnel_open(gid, nid, local, gateway, ip, remote)

    def tunnel_close(self, gid, nid, local, remote_gid, remote_nid, ip, remote):
        """
        Closes a tunnel previously opened by tunnel_open. The `local` port MUST match the
        real open port returned by the tunnel_open function. Otherwise the agent will not match the tunnel and return
        ignore your call.

        Closing a non-existing tunnel is not an error.
        """
        gateway = '%s.%s' % (remote_gid, remote_nid)
        return self._client.tunnel_close(gid, nid, local, gateway, ip, remote)

    def tunnel_list(self, gid, nid):
        """
        Return all opened connection that are open from the agent over the agent-controller it
        received this command from
        """
        return self._client.tunnel_list(gid, nid)
