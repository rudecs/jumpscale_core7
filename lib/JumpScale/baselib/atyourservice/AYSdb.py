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
    type = Column(String, default="local", index=True)
    domain = Column(String, default="", index=True)
    name = Column(String, default="", index=True)
    instance = Column(String, default="", index=True)
    parent = Column(Integer, ForeignKey('service.id'))
    path = Column(String, default="", index=True)
    noremote = Column(Boolean, default="", index=True)
    templatepath = Column(String, default="", index=True)
    cmd = Column(String, default="", index=True)
    priority = Column(Integer, default="", index=True)
    isInstalled = Column(Boolean, default=True, index=True)
    logPath = Column(String, default="", index=True)
    isLatest = Column(Boolean, default=True, index=True)
    children = Column(String, default="", index=True)
    producers = relationship("Producer", backref=backref('service', uselist=False))
    categories = relationship("Category", backref=backref('service', uselist=True))
    hrd = relationship("HRDItem", backref=backref('service', uselist=False))
    tcpPorts = relationship("TCPPort", backref=backref('service', uselist=True))
    servicetemplate = relationship("Template", backref=backref('service', uselist=False))
    processes = relationship("Process", backref=backref('service', uselist=True))
    recipe = relationship("RecipeItem", backref=backref('service', uselist=True))
    dependencies = relationship("Dependency", backref=backref('service', uselist=True))
    sqlite_autoincrement = True


class HRDItem(Base):
    __tablename__ = 'hrd_item'
    id = Column(Integer, primary_key=True)
    service_id = Column(String, ForeignKey('service.id'), nullable=True)
    template_id = Column(String, ForeignKey('template.id'),  nullable=True)
    key = Column(String, default='', index=True)
    value = Column(String, default='', index=True)
    isTemplate = Column(Boolean, default=False, index=True)


class Process(Base):
    __tablename__ = 'process_item'
    id = Column(Integer, primary_key=True)
    service_id = Column(String, ForeignKey('service.id'), nullable=True)
    template_id = Column(String, ForeignKey('template.id'),  nullable=True)
    args = Column(String, default='', index=True)
    cmd = Column(String, default='', index=True)
    cwd = Column(String, default='', index=True)
    filterstr = Column(String, default='', index=True)
    ports = relationship("TCPPort", backref=backref('process', uselist=True))
    priority = Column(String, default="", index=True)
    startupmanager = Column(String, default=False, index=True)
    timeout_start = Column(Integer, default="", index=True)
    timeout_stop = Column(Integer, default="", index=True)
    env = Column(String, default="", index=True)
    name = Column(String, default="", index=True)
    user = Column(String, default="", index=True)
    test = Column(String, default="", index=True)
    isTemplate = Column(Boolean, default=False, index=True)


class RecipeItem(Base):
    __tablename__ = 'recipe_item'
    id = Column(Integer, primary_key=True)
    service_id = Column(String, ForeignKey('service.id'), nullable=True)
    template_id = Column(String, ForeignKey('template.id'),  nullable=True)
    order = Column(String, default='', index=True)
    recipe = Column(String, default='', index=True)
    isTemplate = Column(Boolean, default=False, index=True)


class Dependency(Base):
    __tablename__ = 'dependency'
    id = Column(Integer, primary_key=True)
    service_id = Column(String, ForeignKey('service.id'), nullable=True)
    template_id = Column(String, ForeignKey('template.id'),  nullable=True)
    order = Column(String, default='', index=True)
    domain = Column(String, default='', index=True)
    name = Column(String, default='', index=True)
    instance = Column(String, default='', index=True)
    args = Column(String, default='', index=True)
    isTemplate = Column(Boolean, default=False, index=True)


class Template(Base):
    __tablename__ = 'template'

    id = Column(Integer, primary_key=True)
    type = Column(String, default="local", index=True)
    service_id = Column(Integer, ForeignKey('service.id'), nullable=True)
    domain = Column(String, default="", index=True)
    name = Column(String, default="", index=True)
    instances = relationship("Instance", backref=backref('template', uselist=True))
    metapath = Column(String, default="", index=True)
    instancehrd = Column(String, default="", index=True)
    hrd = relationship("HRDItem", backref=backref('template', uselist=True))
    processes = relationship("Process", backref=backref('template', uselist=True))
    recipe = relationship("RecipeItem", backref=backref('template', uselist=True))
    dependencies = relationship("Dependency", backref=backref('template', uselist=True))


class Producer(Base):
    __tablename__ = 'producer'
    id = Column(Integer, primary_key=True)
    service_id = Column(String, ForeignKey('service.id'))
    key = Column(String, default="", index=True)
    value = Column(String, default="", index=True)

    def __eq__(self, other):
        return self.producer == other.lower()

    def __ne__(self, other):
        return not self.__ne__(other)


class TCPPort(Base):
    __tablename__ = 'tcpport'
    id = Column(Integer, primary_key=True)
    service_id = Column(String, ForeignKey('service.id'), nullable=True)
    process_id = Column(String, ForeignKey('process_item.id'), nullable=True)
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


class Instance(Base):
    __tablename__ = 'instance'
    id = Column(Integer, primary_key=True)
    template_id = Column(String, ForeignKey('template.id'))
    instance = Column(String, default="", index=True)

    def __eq__(self, other):
        return self.instance == other.lower()

    def __ne__(self, other):
        return not self.__ne__(other)
