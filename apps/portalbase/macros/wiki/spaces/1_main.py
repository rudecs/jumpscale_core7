
def main(j, args, params, tags, tasklet):
    params.merge(args)

    doc = params.doc

    out = "{{datatables_use}}\n"

    bullets = params.tags.labelExists("bullets")
    table = params.tags.labelExists("table")
    spaces = [ x.model.id for x in j.core.portal.active.spacesloader.spaces.values() ]
    spaces.sort()


    if params.tags.tagExists("exclude"):
        excludes=params.tags.tagGet("exclude").split(",")
        excludes=[item.strip().lower() for item in excludes]
    else:
        excludes=[]    

    
    for item in spaces:
        if item.lower() not in excludes:
            if table:
                out += "|[%s|/%s]|\n" % (item, item.lower().strip("/"))
            else:
                if item[0] != "_" and item.strip() != "" and item.find("space_system")==-1:
                    if bullets:
                        out += "* [%s|/%s]\n" % (item, item.lower().strip("/"))
                    else:
                        out += "[%s|/%s]\n" % (item, item.lower().strip("/"))

    params.result = (out, doc)

    return params


def match(j, args, params, tags, tasklet):
    return True
