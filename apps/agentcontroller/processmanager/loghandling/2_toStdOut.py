
def main(q, args, params, tags, tasklet):

    print "%s %s" % (args.logobj.category, args.logobj.message)
    return params


def match(q, args, params, tags, tasklet):
    return False
