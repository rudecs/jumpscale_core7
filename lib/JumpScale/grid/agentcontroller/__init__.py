from JumpScale import j

def cb():
    from .AgentControllerFactory import AgentControllerFactory
    return AgentControllerFactory()

j.base.loader.makeAvailable(j, 'clients')
j.clients._register('agentcontroller', cb)
