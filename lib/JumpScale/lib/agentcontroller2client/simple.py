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


class SimpleClient(object):
    def __init__(self, advanced_client):
        self._client = advanced_client

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
