import sys
def main(j, args, params, tags, tasklet):
    params.merge(args)

    j.core.portal.active.restartInProcess(sys.path[0])

    params.result = ("", params.doc)


def match(j, args, params, tags, tasklet):
    return True
