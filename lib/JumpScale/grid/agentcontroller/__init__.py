from JumpScale import j
from .AgentControllerFactory import AgentControllerFactory
j.base.loader.makeAvailable(j, 'clients')
j.clients.agentcontroller = AgentControllerFactory()
