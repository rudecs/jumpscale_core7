from JumpScale import j

def sQLAlchemy():
    from .SQLAlchemy import SQLAlchemyFactory
    return SQLAlchemyFactory()

j.base.loader.makeAvailable(j, 'db')
j.db._register('sqlalchemy', sQLAlchemy)
