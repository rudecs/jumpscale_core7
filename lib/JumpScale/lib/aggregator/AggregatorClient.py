from JumpScale import j
import time
import os
import collections


Stats = collections.namedtuple('Stats', 'measurement h_nr m_nr h_avg m_epoch m_total h_total m_avg m_last epoch ' +
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

    def measure(self, key, measurement, tags, value, timestamp=None):
        """
        @param measurement is what you are measuring e.g. kbps (kbits per sec)
        @param key is well chosen location in a tree structure e.g. key="%s.%s.%s"%(self.nodename,dev,measurement) e.g. myserver.eth0.kbps
           key needs to be unique
        @param tags node:kds dim:iops location:elgouna  : this allows aggregation in influxdb level
        @param timestamp stats timestamp, default to `now`
        """
        return self._measure(key, measurement, tags, value, type="A", timestamp=timestamp)

    def measureDiff(self, key, measurement, tags, value, timestamp=None):
        return self._measure(key, measurement, tags, value, type="D", timestamp=timestamp)

    def _measure(self, key, measurement, tags, value, type, timestamp=None):
        """
        in redis:

        local key=KEYS[1]
        local measurement=ARGV[1]
        local value = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local type=ARGV[4]
        local tags=ARGV[5]
        local node=ARGV[6]

        """
        if timestamp is None:
            timestamp = int(time.time())  # seconds
        res = self.redis.evalsha(self._sha["stat"], 1, key, measurement, value,
                                 str(timestamp), type, tags, self.nodename)

        return res

    def statGet(self, key):
        """
        key is e.g. sda1.iops
        """
        data = self.redis.get("stats:%s:%s" % (self.nodename, key))
        if data == None:
            return {"val": None}

        return Stats(**j.data.serializer.json.loads(data))

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
                yield Stats(**j.data.serializer.json.loads(self.redis.get(key)))

            if cursor == 0:
                break
