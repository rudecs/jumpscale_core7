import shlex
from StringIO import StringIO

import acclient


STATE_UNKNOWN = 'UNKNOWN'
STATE_SUCCESS = 'SUCCESS'
STATE_TIMEDOUT = 'TIMEDOUT'


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

    def execute(self, cmd, path=None, gid=None, nid=None, roles=[], fanout=False, die=True, timeout=5, data=None):
        parts = shlex.split(cmd)
        assert len(parts) > 0, "Empty command string"
        cmd = parts[0]
        args = parts[1:]

        if nid is None and not roles:
            roles = ['*']

        runargs = acclient.RunArgs(max_time=timeout, working_dir=path)
        cmd = self._client.execute(gid, nid, cmd, cmdargs=args, args=runargs, data=data, roles=roles, fanout=fanout)

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
            if job.state != STATE_SUCCESS and die:
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
