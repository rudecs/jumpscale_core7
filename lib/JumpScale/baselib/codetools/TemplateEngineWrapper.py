

from JumpScale import j
from .TemplateEngine import TemplateEngine


class TemplateEngineWrapper(object):
    def new(self):
        return TemplateEngine()