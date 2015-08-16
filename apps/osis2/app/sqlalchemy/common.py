from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Float,
    Integer,
    DateTime)

Base = declarative_base()

class CommonColumns(Base):
    __abstract__ = True
    _created = Column(DateTime, default=func.now())
    _updated = Column(DateTime, default=func.now(), onupdate=func.now())
    _etag = Column(String(40))

typemap = {'str': String,
           'int': Integer,
           'float': Float,
           'dict(str)': String,
           'dict': String,
           'list(str)': String,
           'list': String,
           'list(int)': String,
           'bool': Boolean}

