from JumpScale import j

from .github import GitHubFactory
j.base.loader.makeAvailable(j, 'clients')

j.clients.github=GitHubFactory()
