
def main(j, args, params, tags, tasklet):
    import urlparse
    import urllib

    querystr = args.requestContext.env['QUERY_STRING']
    querytuples = urlparse.parse_qsl(querystr)
    for item in querytuples[:]:
        if item[0] in ['space', 'page']:
            querytuples.remove(item)
    querystr = urllib.urlencode(querytuples)

    page = args.page

    page.addBootstrap()
    page_name = ''

    import re
    page_match = re.search(r"page\s*:\s*([^:}]*)", args.macrostr)
    if page_match:
        page_name = page_match.group(1)

    args = args.tags.getValues(app="", actor="", path="", bucket="", page="", space="", edit=False)

    if page_name == "" and args["path"] == "":
        page.addMessage("ERROR: path needs to be defined in: %s" % params.cmdstr)
        params.result = page
        return params

    if args["app"] != "" and args["actor"] != "":
        # look for path for bucket
        aloader = j.core.portal.active.actorsloader.getActorLoaderFromId("%s__%s" % (args["app"].lower(), args["actor"].lower()))
        path = j.system.fs.joinPaths(aloader.model.path, args["path"])
    elif args["space"] != "":
        # look for path for bucket
        space = j.core.portal.active.getSpace(args["space"])
        if page_name != "":
            space = j.core.portal.active.getSpace(args["space"])
            doc = space.docprocessor.docGet(page_name)
            path = doc.path
            args["edit"] = True
        else:
            path = j.system.fs.joinPaths(space.model.path, args["path"])
    elif args["bucket"] != "":
        # look for path for bucket
        bucket = j.core.portal.active.getBucket(args["bucket"])
        path = j.system.fs.joinPaths(bucket.model.path, args["path"])
    else:
        page.addMessage("ERROR: could not find file as defined in: %s" % params.cmdstr)
        params.result = page
        return params
    if not j.system.fs.exists(path):
        page.addMessage('Supplied path "%s" does not exist.' % args['path'])
        params.result = page
        return params
    content = j.system.fs.fileGetContents(path)

    page.addMessage('<div class="span12">')
    page.addCodeBlock(content, path=path, exitpage=False, edit=args["edit"], spacename=args["space"], pagename=page_name, querystr=querystr)
    page.addMessage('</div>')
    page.addMessage('<div class="span8" style="display: none !important"><iframe space="$space" doc="$doc" id="preview$id" src="/render" width="100%" height="600px"></iframe></div>'.replace('$id', str(page._codeblockid))
                    .replace('$space', args["space"]).replace('$doc', page_name))

    # This macro should be added _only once_ to a page
    page.addJS('/jslib/underscore/underscore.js')
    page.addJS(jsContent='''
    $(function() {
        var render = _.debounce(function() {
            var content = editor1.getValue();
            console.log('Changed');
            var space = $('#preview1').attr('space');
            var doc = $('#preview1').attr('doc');
            $('#preview1').attr('src', '/render?render_space=' + space + '&render_doc=' + doc + '&content=' + encodeURIComponent(content));
        }, 300);
        render();
        //editor1.on('change', render);
    });''')


    params.result = page
    return params


def match(j, args, params, tags, tasklet):
    return True
