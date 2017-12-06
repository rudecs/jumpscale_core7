
def main(q, args, params, tags, tasklet):


    ignore = ['keyboardinterrupt']
    for item in ignore:
        eco = args['eco']
        if hasattr(eco, 'errormessage'):
            if eco.errormessage.find(item) != -1:
                params.stop = True
                params.result=None
                return params

    return params


def match(q, args, params, tags, tasklet):
    return True
