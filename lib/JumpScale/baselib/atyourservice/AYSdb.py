from JumpScale import j
from sqlalchemy.orm import relationship, backref, sessionmaker, class_mapper
from sqlalchemy import *
from sqlalchemy.event import listen
from sqlalchemy.orm.collections import attribute_mapped_collection

db = j.db.sqlalchemy
Base = db.getBaseClass()

service_to_service = Table("service_to_service", Base.metadata,
    Column("child_service_id", Integer, ForeignKey("service.id"), primary_key=True),
    Column("parent_service_id", Integer, ForeignKey("service.id"), primary_key=True)
)

template_to_template = Table("template_to_template", Base.metadata,
    Column("child_template_id", Integer, ForeignKey("template.id"), primary_key=True),
    Column("parent_template_id", Integer, ForeignKey("template.id"), primary_key=True)
)

class Service(Base):
    __tablename__ = 'service'
    id = Column(Integer, primary_key=True, nullable=False)
    domain = Column(String, default="", index=True)
    name = Column(String, default="", index=True)
    isntance = Column(String, default="", index=True)
    parent = Column("Service", ForeignKey('service.id'))
    path = Column(String, default="", index=True)
    noremote = Column(Boolean, default="", index=True)
    templatepath = Column(String, default="", index=True)
    cmd = Column(String, default="", index=True)
    priority = Column(Integer, default="", index=True)
    isInstalled = Column(Boolean, default=True, index=True)
    logPath = Column(String, default="", index=True)
    isLatest = Column(Boolean, default=True, index=True)
    hrd = Column(Integer, ForeignKey('hrd.id'), nullable=False)
    producers = relationship("Producer", backref=backref('service', uselist=False))
    categories = relationship("Category", backref=backref('service', uselist=True))
    hrddata = relationship("HRDdata", backref=backref('service', uselist=False))
    tcpPorts = relationship("TCPPort", backref=backref('service', uselist=True))
    servicetemplate = relationship("Template", backref=backref('service', uselist=False))
    args = relationship("Args", backref=backref('service', uselist=False))
    parents = relationship("Service",
                        secondary="service_to_service",
                        primaryjoin="Service.id==service_to_service.c.child_service_id",
                        secondaryjoin="Service.id==service_to_service.c.parent_service_id",
                        backref="service_parents")
    dependencies = relationship("Service",
                        secondary="service_to_service",
                        primaryjoin="Service.id==service_to_service.c.parent_service_id",
                        secondaryjoin="Service.id==service_to_service.c.child_service_id",
                        backref="service_dependencies")
    children = relationship("Service",
                        secondary="service_to_service",
                        primaryjoin="Service.id==service_to_service.c.parent_service_id",
                        secondaryjoin="Service.id==service_to_service.c.child_service_id",
                        backref="service_children")
    sqlite_autoincrement = True


# class HRDItem(Base):
#     __tablename__ = 'template_hrd_item'
#     id = Column(Integer, primary_key=True)
#     name = 
#     temmplate_id ...
#     value = json
#     isTemplate = bool


# class Process
#     isTemplate = bool

# ...

# RecipeItem

# class Template(Base):
#     __tablename__ = 'template'

#     id = Column(Integer, primary_key=True)
#     service_id = Column(Integer, ForeignKey('service.id'))
#     domain = Column(String, default="", index=True)
#     name = Column(String, default="", index=True)
#     instances = relationship("Instance", backref=backref('template', uselist=True))
#     metapath = Column(String, default="", index=True)
#     hrd = relationship("HRDItem", backref=backref('template', uselist=True))
#     process
#     ...
#     parent = Column(Integer, ForeignKey('template.id'), nullable=True, default='')


class Producer(Base):
    __tablename__ = 'producer'
    id = Column(Integer, primary_key=True)
    service_id = Column(String, ForeignKey('service.id'))
    producer = Column(PickleType)

    def __eq__(self, other):
        return self.producer == other.lower()

    def __ne__(self, other):
        return not self.__ne__(other)

class TCPPort(Base):
    __tablename__ = 'tcpport'
    id = Column(Integer, primary_key=True)
    service_id = Column(String, ForeignKey('service.id'))
    tcpport = Column(Integer, default="", index=True)

    def __eq__(self, other):
        return self.tcpport == other.lower()

    def __ne__(self, other):
        return not self.__ne__(other)

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    service_id = Column(String, ForeignKey('service.id'))
    category = Column(String, default="", index=True)

    def __eq__(self, other):
        return self.category == other.lower()

    def __ne__(self, other):
        return not self.__ne__(other)

