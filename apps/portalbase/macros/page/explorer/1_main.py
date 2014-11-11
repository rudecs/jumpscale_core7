
def main(j, args, params, tags, tasklet):
    import os
    page = args.page
    params.result = page

    path = ''
    space = args.paramsExtra.get('space')
    if space:
        space = j.core.portal.active.getSpace(space)
        path = os.path.join(j.core.portal.active.cfgdir.rpartition('/')[0], 'wiki', space.model.id)

    if args.tags.tagExists("ppath"):
        path = args.tags.tagGet("ppath").replace("+", ":").replace("___", ":").replace("\\", "/")
        if not j.system.fs.exists(path):
            page.addMessage("ERROR:could not find file %s" % path)

        apppath = j.core.portal.active.cfgdir.rpartition('/')[0]
        codepath = os.getcwd()
        if path.startswith('/') and not (path.startswith(apppath) or path.startswith(codepath)):
            path = ''

    if args.tags.tagExists("bucket"):
        bucket = args.tags.tagGet("bucket").lower()

        if bucket not in j.core.portal.active.bucketsloader.buckets:
            page.addMessage("Could not find bucket %s" % bucket)
            return params
        bucket = j.core.portal.active.bucketsloader.buckets[bucket]
        path = bucket.model.path.replace("\\", "/")

    if args.tags.tagExists("height"):
        height = int(args.tags.tagGet("height"))
    else:
        height = 500

    if args.tags.tagExists("key"):
        key = args.tags.tagGet("key")
    else:
        key = None

    if args.tags.tagExists("readonly") or args.tags.labelExists("readonly"):
        readonly = True
    else:
        readonly = False

    if args.tags.tagExists("tree") or args.tags.labelExists("tree"):
        tree = True
    else:
        tree = False

    if path == "$$path":
        params.page.addMessage("Could not find path to display explorer for")
        return params

    page.addExplorer(path, dockey=key, height=height, readonly=readonly, tree=tree)

    return params


def match(j, args, params, tags, tasklet):
    return True
