
def main(q, args, params, tags, tasklet):


    ignore = ['keyboardinterrupt']
    for item in ignore:
        if args["eco"].errormessage.find(item) <> -1:
            params.stop = True
            params.result=None
            return params

    return params


def match(q, args, params, tags, tasklet):
    return True
