import re

def main(j, args, params, tags, tasklet):
    page = args.page
    doc = args.doc
    page.addCSS('/jslib/old/breadcrumbs/breadcrumbs.css')    

    separator = '<i class="separator"></i>'
    breadcrumbs = [doc.original_name]
    space = j.core.portal.active.getSpace(doc.getSpaceName())
    while doc.parent:
        doc = space.docprocessor.name2doc.get(doc.parent)
        if not doc:
            break
        breadcrumbs.insert(0, doc.original_name)

    page.addMessage(separator.join('<a href="/$$space/{0}">{0}</a>'.format(b) for b in breadcrumbs))
    params.result = page
    return params


def match(j, args, params, tags, tasklet):
    return True
