from JumpScale import j

def statag():
    from .StatAggregator import StatAggregator
    return StatAggregator()

def statred():
    from .redisstataggregator import RedisStatAggregator
    return RedisStatAggregator()

j.base.loader.makeAvailable(j, 'system')
j.system._register('stataggregator', statag)
j.system._register('redisstataggregator', statred)

