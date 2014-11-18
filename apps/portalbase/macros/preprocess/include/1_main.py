def main(j, args, params,  tags, tasklet):
    params.merge(args)

    doc = params.doc
    tags = params.tags
    params.result = ""

    if not tags.tagExists("include"):
        raise RuntimeError("include command not found in %s" % tags)

    name = tags.tagGet("include")

    if tags.tagExists("type"):
        type = tags.tagGet("type")
    else:
        type = ""

    if tags.tagExists("heading"):
        headinglevel = tags.tagGet("heading")
    else:
        headinglevel = None

    name = name.lower()
    if type != "":

        if "%s_%s" % (name, type) in doc.preprocessor.nametype2doc:
            # found the page to include
            doc2 = doc.preprocessor.nametype2doc["%s_%s" % (name, type)]
        else:
            #doc.preprocessor.errorTrap("include %s not found in %s" % (name,tags))
            msg = "**ERROR**: include %s not found in %s" % (name, tags)
            print(msg)
            params.result = (msg, doc)
            return params
    else:
        if name in doc.preprocessor.name2doc:
            # found the page to include
            doc2 = doc.preprocessor.name2doc[name].copy()
        else:
            #doc.preprocessor.errorTrap("include %s not found in %s" % (name,tags))
            msg = "**ERROR**: include %s not found in %s" % (name, tags)
            print(msg)
            params.result = (msg, doc)
            return params

    doc2.loadFromDisk()

    if headinglevel != None:
        doc2.fixMinHeadingLevel(headinglevel)

    if doc2.visible:
        # make sure we restart from original source when doing the includes (only for include we do this)
        params.result = (doc2.source, doc)
        if params.tags.labelExists("title"):
            if headinglevel == None:
                headinglevel = 2

            params.result = ("h%s. %s\n%s" % (headinglevel, doc2.title, doc2.source), doc)
    else:
        params.result = ("", doc)
    

    return params


def match(j, args, params,  tags, tasklet):
    return True
