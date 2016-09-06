from JumpScale import j
import time
import json
import os
import collections


Stats = collections.namedtuple('Stats', 'h_nr m_nr h_avg m_epoch m_total h_total m_avg m_last epoch ' +
                               'm_max val h_max key tags h_epoch')

Log = collections.namedtuple('Log', 'level message node epoch tags')


class AggregatorClient:

    def __init__(self, redis, nodename):
        self.redis = redis
        self._sha = dict()

        path = os.path.dirname(__file__)
        luapaths = j.system.fs.listFilesInDir(path, recursive=False, filter="*.lua", followSymlinks=True)
        for luapath in luapaths:
            basename = j.system.fs.getBaseName(luapath).replace(".lua", "")
            lua = j.system.fs.fileGetContents(luapath)
            self._sha[basename] = self.redis.script_load(lua)

        self.nodename = nodename

    def measure(self, key, tags, value, timestamp=None):
        """
        @param key is well chosen location in a tree structure e.g. key="%s.%s"%(self.nodename,dev) e.g. myserver.eth0
           key needs to be unique
        @param tags node:kds dim:iops location:elgouna  : this allows aggregation in influxdb level
        @param timestamp stats timestamp, default to `now`
        """
        return self._measure(key, tags, value, type="A", timestamp=timestamp)

    def measureDiff(self, key, tags, value, timestamp=None):
        return self._measure(key, tags, value, type="D", timestamp=timestamp)

    def _measure(self, key, tags, value, type, timestamp=None):
        """
        in redis:

        local key=KEYS[1]
        local value = tonumber(ARGV[1])
        local now = tonumber(ARGV[2])
        local type=ARGV[3]
        local tags=ARGV[4]
        local node=ARGV[5]

        """
        if timestamp is None:
            timestamp = int(time.time())  # seconds
        res = self.redis.evalsha(self._sha["stat"], 1, key, value,
                                 str(timestamp), type, tags, self.nodename)

        return res

    def statGet(self, key):
        """
        key is e.g. sda1.iops
        """
        data = self.redis.get("stats:%s:%s" % (self.nodename, key))
        if data is not None:
            return {"val": None}

        return Stats(**json.loads(data))

    @property
    def stats(self):
        """
        iterator to go over stat objects
        """
        cursor = 0
        match = 'stats:%s:*' % self.nodename
        while True:
            cursor, keys = self.redis.scan(cursor, match)
            for key in keys:
                yield Stats(**json.loads(self.redis.get(key)))

            if cursor == 0:
                break
