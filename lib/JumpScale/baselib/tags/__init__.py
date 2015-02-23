from JumpScale import j

def cb():
    from .TagsFactory import TagsFactory
    return TagsFactory()

j.core._register('tags', cb)
