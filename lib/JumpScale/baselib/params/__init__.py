from JumpScale import j

def cb():
    from .Params import ParamsFactory
    return ParamsFactory()

j.core._register('params', cb)
