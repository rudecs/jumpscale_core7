
def main(j, args, params, tags, tasklet):

    doc = args.doc

    params.result = ""
    spaces = [ x.model.id for x in j.core.portal.active.spacesloader.spaces.values() ]
    spaces.sort()

    C = "{{menudropdown: %s\n" % args.tags
    for space in spaces:
        C += "%s:/%s\n" % (space, space)
    C += "}}\n"

    if j.core.portal.active.isAdminFromCTX(args.requestContext):
        params.result = C

    params.result = (params.result, doc)

    return params


def match(j, args, params, tags, tasklet):
    return True
