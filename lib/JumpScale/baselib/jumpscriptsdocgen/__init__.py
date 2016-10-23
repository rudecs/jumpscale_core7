from JumpScale import j

def cb():
    from .jumpscriptsdocgen import JumpscriptsDocumentGenerator
    return JumpscriptsDocumentGenerator()

j.base.loader.makeAvailable(j, 'tools')
j.tools._register('jumpscriptsdocgen', cb)
