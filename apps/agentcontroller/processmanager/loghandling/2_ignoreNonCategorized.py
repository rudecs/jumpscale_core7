
def main(q, args, params, tags, tasklet):

    if args.logobj.category == "":
        params.stop = True
        params.result=None

    return params


def match(q, args, params, tags, tasklet):
    return False
