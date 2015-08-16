from app.sqlalchemy.common import CommonColumns, typemap
import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    ForeignKey,
    DateTime)



class employee(CommonColumns):
    __tablename__ = 'employee'
    guid = Column(String(36), primary_key=True)

    id = Column(typemap['str'], nullable=True)
    domain = Column(typemap['str'])
    gid = Column(typemap['int'])
    passwd = Column(typemap['str'])
    roles = Column(typemap['list'])
    active = Column(typemap['bool'])
    description = Column(typemap['str'])
    emails = Column(typemap['list'])
    xmpp = Column(typemap['list'])
    mobile = Column(typemap['list'])
    lastcheck = Column(typemap['int'])
    groups = Column(typemap['list'])
    authkey = Column(typemap['str'])
    data = Column(typemap['str'])
    authkeys = Column(typemap['list'])