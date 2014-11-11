
def main(j, params, service, tags, tasklet):

    doc = params.doc
    tags = params.tags

    # a preprocess macro manipulates the doc object
    # a preprocess macro is loaded when the appserver starts or when content is changed (not when a user requests content)

    doc.content = "TEST all the rest is gone"

    return params


def match(j, params, service, tags, tasklet):
    return True
