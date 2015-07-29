def pre_create(items):
    for item in items:
        item['domain'] = 'newdomain'

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
