
def main(j, args, params, tags, tasklet):

    params.merge(args)

    page = params.page
    tags = params.tags
    import ipdb; ipdb.set_trace()

    for item in j.core.portal.active.bucketsloader.buckets.keys():
        params.page.addBullet(item, 1)

    params.result = page

    return params


def match(j, args, params, tags, tasklet):
    return True
