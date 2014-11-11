
def main(j, args, params, tags, tasklet):
    params.result = args.page
    tags = args.tags
    disable_filters = tags.tagExists('disable_filters') and tags.tagGet('disable_filters').lower() == 'true'

    modifier = j.html.getPageModifierGridDataTables(args.page)
    modifier.prepare4DataTables()
    if not disable_filters:
        modifier.addSearchOptions()

    return params


def match(j, args, params, tags, tasklet):
    return True
