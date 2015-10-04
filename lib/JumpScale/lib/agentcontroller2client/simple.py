import os
import shlex
from StringIO import StringIO

import acclient


class SimpleClient(object):
    def __init__(self, advanced_client):
        self._client = advanced_client

    def _concat_levels(self, msgs, *levels):
        buffers = {}
        for l in levels:
            buffers[l] = StringIO()

        for i in xrange(len(msgs) - 1, -1, -1):
            msg = msgs[i]
            if msg['level'] not in levels:
                continue

            buff = buffers[msg['level']]
            buff.write(msg['data'])
            buff.write(os.linesep)

        return map(lambda l: buffers[l].getvalue(), levels)

    def execute(self, cmd, path=None, gid=None, nid=None, roles=['*'], fanout=False, die=True, timeout=5, data=None):
        parts = shlex.split(cmd)
        assert len(parts) > 0, "Empty command string"
        cmd = parts[0]
        args = parts[1:]

        runargs = acclient.RunArgs(max_time=timeout, working_dir=path)
        cmd = self._client.execute(gid, nid, cmd, cmdargs=args, args=runargs, data=data, roles=roles, fanout=fanout)

        results = []
        for job in cmd.iter_results(timeout):
            stdout, stderr = job.streams
            if job.state != 'SUCCESS' and die:
                error = job.data or stderr
                raise acclient.AgentException(
                    'Job on agent {job.gid}.{job.nid} failed with status: "{job.state}" and message: "{error}"'.format(job=job, error=error)
                )

            results.append((job.state, stdout, stderr))

        if fanout:
            # potential multiple results.
            return results
        else:
            return results.pop()
