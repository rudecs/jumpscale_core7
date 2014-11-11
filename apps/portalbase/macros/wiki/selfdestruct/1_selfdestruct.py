
def main(j, args, params, tags, tasklet):
    params.merge(args)

    params.result = ""

    doc = params.doc

    if doc.content.find("@DESTRUCTED@") != -1:
        # page no longer show, destruction message
        doc.destructed = True
        doc.content = doc.content.replace("@DESTRUCTED@", "")

    else:
        if doc.destructed == False:
            newdoc = "@DESTRUCTED@\n%s" % j.system.fs.fileGetContents(params.doc.path)
            doc.todestruct = True
            j.system.fs.writeFile(params.doc.path, newdoc)

    params.result = ("", params.doc)

    return params


def match(j, args, params, tags, tasklet):
    return True
