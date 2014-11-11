
def main(j, args, params, tags, tasklet):
    params.merge(args)

    doc = params.doc

    params.result = ""

    bullets = params.tags.labelExists("bullets")

    if params.tags.tagExists("depth"):
        depth = params.tags.tagGet("depth")
    else:
        depth = 0

    if params.tags.tagExists("page"):
        page = params.tags.tagGet("page")
    else:
        page = None

    if page != None:
        if doc.preprocessor.docExists(page):
            doc = doc.preprocessor.docGet(page)
        else:
            params.result = "MACRO CHILDREN ERROR: Could not find page with name %s to start from." % page

    if depth != 0:
        names = [j.system.fs.getBaseName(item).replace(".wiki", "") for item in j.system.fs.listFilesAndDirsInDir(j.system.fs.getDirName(doc.path),
                                                                                                                  True, filter="*.wiki", depth=depth, type="fd")]  # @todo implement depth

    else:
        names = []
        for doc in doc.children:
            names.append(j.system.fs.getBaseName(doc.path).replace(".wiki", ""))
    for name in sorted(names, key=lambda name: name.lower()):
        if name[0] != ".":
            if bullets:
                params.result += "* [%s|%s]\n" % (name, "/%s/%s" % (doc.getSpaceName(), name))
            else:
                params.result += "[%s|%s]\n" % (name, "/%s/%s" % (doc.getSpaceName(), name))

    # bullets=True
    #names=[j.system.fs.getBaseName(item).replace(".wiki","") for item in j.system.fs.listFilesInDir(j.system.fs.getDirName(doc.path),False,filter="*.wiki")]
    # names=j.system.fs.listDirsInDir(j.system.fs.getDirName(doc.path),False)
    # for name in names:
        # if name.lower()<>doc.name:
            # if name.find("wiki")==0:
                # name=name[5:]
            # if bullets:
                #params.result += "* [%s]\n"%name.replace("\\","/")
            # else:
                #params.result += "[%s]\n"%name.replace("\\","/")
    params.result = (params.result, params.doc)

    return params


def match(j, args, params, tags, tasklet):
    return True
