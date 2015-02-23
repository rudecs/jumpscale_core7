from JumpScale import j

def cb():
    from .Cuisine import OurCuisine
    return OurCuisine()

j.base.loader.makeAvailable(j, 'remote')
j.remote._register('cuisine', cb)
