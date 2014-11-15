from JumpScale import j
from .StatAggregator import StatAggregator
from .redisstataggregator import RedisStatAggregator

j.base.loader.makeAvailable(j, 'system')
j.system.stataggregator = StatAggregator()
j.system.redisstataggregator = RedisStatAggregator()

