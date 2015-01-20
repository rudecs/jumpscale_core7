from JumpScale import j

descr = """list jpackage action_jpackage"""

name = "jpackage_list"
category = "jpackages"
organization = "jumpscale"
author = "deboeckj@incubaid.com"
version = "1.0"
roles = []

def action(domain):
    if not domain:
        packages = j.packages.find(domain='', name='')
    else:
         dobj = j.packages.getDomainObject(domain)
         packages = dobj.getJPackages()
    result = list()
    fields = ('name', 'domain', 'version')
    for package in packages:
        pdict = dict()
        for field in fields:
            pdict[field] = getattr(package, field)
        pdict['installed'] = package.isInstalled()
        result.append(pdict)
    return result
