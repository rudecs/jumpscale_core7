from JumpScale import j
from .HRDFactory import HRDFactory
from ..tags.TagsFactory import TagsFactory

# j.base.loader.makeAvailable(j, 'core')
j.core.hrd = HRDFactory()
