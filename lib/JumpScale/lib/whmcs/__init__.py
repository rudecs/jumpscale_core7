
from JumpScale import j
j.base.loader.makeAvailable(j, 'tools.whmcs')
from whmcsorders import whmcsorders
from whmcstickets import whmcstickets
from whmcsusers import whmcsusers

j.tools.whmcs.orders = whmcsorders()
j.tools.whmcs.tickets = whmcstickets()
j.tools.whmcs.users = whmcsusers()
