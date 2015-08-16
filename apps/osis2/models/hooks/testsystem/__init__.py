from JumpScale import j
import datetime

##############################################
# Generic Hooks to be run on namespace level #
# For all objects in this namespace 
##############################################

def pre_create(items):
    """
    Auto generate guid if already does not exist
    """
    for item in items:
        if not item.get('guid'):
            item['guid'] = j.base.idgenerator.generateGUID()
        item['lastupdatedat'] = datetime.datetime.now()

def post_create(items):
    pass

def pre_replace(item, original):
    pass

def post_replace(item, original):
    pass

def pre_update(item, original):
    item['lastupdatedat'] = datetime.datetime.now()

def post_update(updates, original):
    pass

def pre_delete(item):
    pass

def post_delete(item):
    pass

def get(response):
    pass
