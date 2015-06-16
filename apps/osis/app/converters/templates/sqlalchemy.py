from app.sqlalchemy.common import CommonColumns, typemap
import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    ForeignKey,
    DateTime)

{% for modelname, modelspec in spec.iteritems() %}

class {{modelname}}(CommonColumns):
    __tablename__ = '{{modelname.lower()}}'
    guid = Column(String(36), primary_key=True)
{% for propspec in modelspec.properties %}
    {{propspec.name}} = Column(typemap['{{propspec.ttype}}'])
{%- endfor %}
{% endfor %}
