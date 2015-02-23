from JumpScale import j

def whmcsorders():
    from .whmcsorders import whmcsorders
    return whmcstickets()

def whmcsusers():
    from .whmcsusers import whmcsusers
    return whmcsusers()

def whmcstickets():
    from .whmcstickets import whmcstickets
    return whmcstickets()

j.base.loader.makeAvailable(j, 'tools.whmcs')
j.tools.whmcs._register('orders', whmcsorders)
j.tools.whmcs._register('tickets', whmcstickets)
j.tools.whmcs._register('users', whmcsusers)
