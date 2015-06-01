from JumpScale import j

descr = """list atyourservice templates"""

category = "ays"
organization = "jumpscale"
author = "khamisr@codescalers.com"
version = "1.0"
roles = []


def action(domain="", name="", category="", reload=False):
    import re
    import json

    def _getTemplates():
        templates = rcl.hgetalldict("ays:templates")
        if domain or name:
            key = '%s_%s' % (domain or '[a-zA-Z0-9]*', name or '[a-zA-Z0-9]*')
            regex = re.compile(key)
            matched = [m.string for template in templates.keys()
                       for m in [regex.search(template)] if m]
            return [templates[m] for m in matched]
        else:
            return templates

    rcl = j.clients.redis.getByInstance("system")
    if rcl.exists("ays:templates") and not reload:
        templates = rcl.hgetalldict("ays:templates")
        if templates:
            return _getTemplates()

    templates = j.atyourservice.findTemplates(domain, name)
    fields = ("name", "domain", "metapath")
    for template in templates:
        tdict = dict()
        for field in fields:
            tdict[field] = getattr(template, field)
        tdict["instances"] = template.listInstances()
        rcl.hset("ays:templates", "%(domain)s_%(name)s" %
                 tdict, json.dumps(tdict))
    return _getTemplates()
