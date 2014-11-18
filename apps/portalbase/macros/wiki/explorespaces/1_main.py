import os
import urllib.request, urllib.parse, urllib.error


def main(j, args, params, tags, tasklet):
    params.merge(args)

    out = ""

    spaces = j.core.portal.active.spacesloader.spaces

    for spacename in sorted(spaces.keys()):
        model = spaces[spacename].model  # @todo security breach
        path = os.path.abspath(model.path)
        querystr = urllib.parse.urlencode({'ppath': path})

        out += "| [%s | /system/Explorer?%s] | [Reload | /system/ReloadSpace?name=%s]|\n" % \
            (model.id, querystr, model.id)

    params.result = (out, params.doc)

    return params


def match(j, args, params, tags, tasklet):
    return True
