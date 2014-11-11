
def main(j, args, params, tags, tasklet):
    params.merge(args)

    if params.tags.tagExists("height"):
        height = int(params.tags.tagGet("height"))
    else:
        height = 400

    if params.tags.tagExists("docname"):
        docname = params.tags.tagGet("docname")
        doc = params.doc.preprocessor.docGet(docname)
        path = j.system.fs.getDirName(doc.path)
    else:
        path = j.system.fs.getDirName(params.doc.path)

    if j.system.fs.exists(j.system.fs.joinPaths(path, "files")):
        path = j.system.fs.joinPaths(path, "files")

    if params.tags.tagExists("readonly") or params.tags.labelExists("readonly"):
        readonly = " readonly"
    else:
        readonly = ""

    path = path.replace(":", "+")

    out = "{{explorer: ppath:%s height:%s key:%s %s}}" % (path, height, params.doc.getPageKey(), readonly)

    params.result = (out, params.doc)

    return params


def match(j, args, params, tags, tasklet):
    return True
