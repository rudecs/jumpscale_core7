from .helpers import roshelpers

def pre_create(items):
    """
    Override the default behavior for guid generation in case of NODE
    so that guid cnontains the gid_guid
    """
    for item in items:
        item['id'] = roshelpers.increment('system.node')
        item['guid'] = "%s_%s" % (item['gid'], item['id'])

def post_create(items):
    pass

def pre_replace(item, original):
    pass

def post_replace(item, original):
    pass

def pre_update(updates, original):
    pass

def post_update(updates, original):
    pass

def pre_delete(item):
    pass

def post_delete(item):
    pass

def get(response):
    pass
