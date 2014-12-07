from JumpScale import j
j.base.loader.makeAvailable(j, 'client')
from .PostgresqlFactory import PostgresqlFactory
j.client.postgres=PostgresqlFactory()